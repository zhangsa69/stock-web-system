"""
Hermes 桥接层 — 通过 Hermes Agent CLI 调用完整 skill 链

两步流水线:
  1. cninfo-financial-analysis → Markdown 分析报告
  2. md2html → 精美 HTML
"""
import asyncio
import base64
import logging
import re
import shlex
import traceback
from ..config import settings

logger = logging.getLogger("stock-analysis.hermes")


class HermesBridge:
    """通过 docker exec 调用 Hermes Agent CLI 执行 skill 链"""

    def __init__(self):
        self.timeout = settings.hermes_timeout
        self.container = getattr(settings, "hermes_container", "hermes-agent")
        self.hermes_bin = "/opt/hermes/.venv/bin/hermes"

    async def _docker_exec(self, command: str, timeout: int, env: dict | None = None) -> dict:
        """在 hermes-agent 容器内执行命令"""
        env_args = []
        if env:
            for k, v in env.items():
                env_args.extend(["-e", f"{k}={v}"])

        cmd = ["docker", "exec", *env_args, self.container, "bash", "-c", command]
        logger.info("[BRIDGE][EXEC] %s", " ".join(cmd))

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info("[BRIDGE][PROC] pid=%s", process.pid)

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            logger.info(
                "[BRIDGE][DONE] pid=%s rc=%s stdout=%d stderr=%d",
                process.pid, process.returncode, len(stdout_text), len(stderr_text),
            )
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": process.returncode,
            }
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.error("[BRIDGE][TIMEOUT] pid=%s timeout=%ds", process.pid, timeout)
            return {"success": False, "stdout": "", "stderr": f"超时（{timeout}秒）", "exit_code": -1}
        except Exception:
            process.kill()
            await process.wait()
            logger.error("[BRIDGE][EXCEPTION] %s", traceback.format_exc())
            return {"success": False, "stdout": "", "stderr": "内部异常", "exit_code": -1}

    def _extract_agent_response(self, raw: str) -> str:
        """从 hermes chat -Q 输出中提取最终回复（去掉 session info 和 diff artifacts）"""
        lines = raw.strip().split("\n")
        cleaned = []
        for line in lines:
            s = line.strip()
            # 跳过 session info
            if re.match(r"^(Session|session):\s*\S", s):
                continue
            # 跳过多余空行
            if not s and cleaned and not cleaned[-1]:
                continue
            cleaned.append(line)
        result = "\n".join(cleaned).strip()
        # 清洗 diff 标记（agent 用 patch 写文件时留下的）
        result = self._strip_diff_artifacts(result)
        return result

    def _strip_diff_artifacts(self, text: str) -> str:
        """去除 agent 输出中混杂的 diff/git 格式标记"""
        lines = text.split("\n")
        out = []
        in_diff = False
        for line in lines:
            s = line.strip()
            # diff 头部标记
            if s.startswith("┊ review diff") or s.startswith("review diff"):
                in_diff = True
                continue
            if s.startswith("a//") or s.startswith("b//"):
                continue
            if re.match(r"^@@\s+-", s):
                continue
            if s in ("---", "+++"):
                continue
            if s.startswith("index ") or s.startswith("diff --git"):
                continue
            # 空行结束 diff 块
            if in_diff and not s:
                in_diff = False
                continue
            if in_diff:
                # 还原被 diff 修饰的行（去掉前缀 +/-/空格）
                if s.startswith("+") and len(s) > 1:
                    out.append(s[1:])
                elif s.startswith("-"):
                    continue  # 删除行不保留
                elif s.startswith(" "):
                    out.append(s[1:])
                else:
                    out.append(line)
            else:
                out.append(line)
        return "\n".join(out).strip()

    async def _call_skill(self, prompt: str, skills: list[str], timeout: int, max_turns: int = 50) -> dict:
        """调用 hermes chat 执行指定的 skills"""
        skills_args = " ".join(f"-s {shlex.quote(s)}" for s in skills)
        cmd = (
            f"{self.hermes_bin} chat "
            f"-q {shlex.quote(prompt)} "
            f"{skills_args} "
            f"--yolo -Q "
            f"--max-turns {max_turns}"
        )
        logger.info("[BRIDGE][SKILL_CALL] skills=%s timeout=%s", skills, timeout)
        return await self._docker_exec(cmd, timeout=timeout)

    async def run_skill(
        self,
        skill_name: str,
        stock_code: str,
        timeout: int | None = None,
    ) -> dict:
        """
        单步流水线: cninfo-financial-analysis 生成 Markdown → 直接返回

        Returns:
            {"success": bool, "report": str, "html_report": str, "error": str | None}
        """
        total_timeout = timeout or self.timeout
        md_path = f"/tmp/analysis_{stock_code}.md"

        # ═══════ 财报分析 → Markdown ═══════
        prompt = (
            f"分析股票 {stock_code}。"
            f"按 cninfo-financial-analysis 流程完成完整分析"
            f"（下载财报、NotebookLM 分析、排雷、市场数据交叉验证）。"
            f"分析完成后，把完整报告用 write_file 写入 {md_path}。"
        )
        logger.info("[BRIDGE][STEP1] 分析 | stock=%s timeout=%s", stock_code, total_timeout)
        result = await self._call_skill(prompt, ["cninfo-financial-analysis"], total_timeout, max_turns=50)

        if not result["success"]:
            err = result["stderr"] or result["stdout"] or "Hermes Agent 执行失败"
            logger.error("[BRIDGE][FAIL] stock=%s err=%s", stock_code, err[:500])
            return {"success": False, "report": "", "html_report": "", "error": f"分析失败: {err[:500]}"}

        # 从文件读取 — 不依赖 Agent 文本输出（可能被 diff 污染）
        read_md = await self._docker_exec(f"cat {md_path}", timeout=10)
        if read_md["success"] and read_md["stdout"].strip():
            markdown = read_md["stdout"]
        else:
            markdown = self._extract_agent_response(result["stdout"])
            if not markdown:
                markdown = result["stdout"].strip()

        logger.info("[BRIDGE][OK] stock=%s md_len=%d", stock_code, len(markdown))

        # 清理临时文件
        await self._docker_exec(f"rm -f {md_path}", timeout=5)

        return {
            "success": True,
            "report": markdown,
            "html_report": "",
            "error": None,
        }


# 全局实例
hermes_bridge = HermesBridge()
