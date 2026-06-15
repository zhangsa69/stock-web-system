"""
Hermes 桥接层 — 直接执行 CNinfo → NotebookLM 流水线

通过 docker exec 在 hermes-agent 容器内运行实际的财报分析命令。
不再依赖不存在的 `hermes skill` CLI 子命令。
"""
import asyncio
import logging
import random
import re
import traceback
from ..config import settings

logger = logging.getLogger("stock-analysis.hermes")

MOCK_REPORTS = {
    "default": """## 📊 {stock_code} 财务分析报告

### 一、公司概况
该公司近年经营状况稳定，所处行业景气度处于上升周期。

### 二、盈利能力分析（近5年）
| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 |
|------|------|------|------|------|------|
| 营业收入(亿) | 285.6 | 312.3 | 338.9 | 367.2 | 401.5 |
| 净利润(亿)   | 42.8  | 48.1  | 52.6  | 58.3  | 64.7  |
| 毛利率(%)    | 35.2  | 36.1  | 37.4  | 38.2  | 39.1  |
| 净利率(%)    | 15.0  | 15.4  | 15.5  | 15.9  | 16.1  |
| ROE(%)       | 18.2  | 18.9  | 19.5  | 20.1  | 20.8  |

> 营收5年复合增长率约 8.9%，净利润复合增长率约 10.9%，盈利能力持续提升。

### 三、资产负债分析
- **资产负债率**：约 42%，处于行业合理水平
- **流动比率**：1.85，短期偿债能力良好
- **经营现金流**：持续为正，5年均值 52 亿

### 四、风险提示
1. 行业竞争加剧可能导致毛利率承压
2. 原材料价格波动对成本端的影响
3. 宏观经济不确定性带来的需求波动

### 五、综合评价
该公司财务基本面扎实，盈利能力稳健增长，现金流健康。建议关注行业政策变化及季报数据更新。

---
*本报告由 AI 自动生成，仅供参考，不构成投资建议。*
""",
}

# ─── Analysis prompt template ───
ANALYSIS_PROMPT_TEMPLATE = """请以财务分析师的视角，对该公司进行全面深度分析。包括：
1）公司概况和主营业务
2）盈利能力分析（毛利率、净利率、ROE趋势）
3）成长性分析（营收和利润增长率）
4）财务健康度（资产负债率、现金流状况）
5）排雷分析：是否存在财务造假或暴雷风险
6）当前估值是否合理（击球区判断）
请给出具体数据和结论。"""


class HermesBridge:
    """通过 docker exec 在 hermes-agent 容器内执行 CNinfo 流水线"""

    def __init__(self):
        self.timeout = settings.hermes_timeout
        self.mock_mode = settings.hermes_mock
        self.cninfo_project = getattr(settings, "cninfo_project_dir", "/opt/data/CNinfo2Notebookllm")
        self.notebooklm_dir = getattr(settings, "notebooklm_dir", "/opt/data/home/.notebooklm")
        # hermes-agent 容器名（可通过 .env 配置）
        self.container = getattr(settings, "hermes_container", "hermes-agent")

    async def _docker_exec(self, command: str, timeout: int, env: dict | None = None) -> dict:
        """在 hermes-agent 容器内执行命令，返回 {success, stdout, stderr, exit_code}"""
        env_args = []
        if env:
            for k, v in env.items():
                env_args.extend(["-e", f"{k}={v}"])

        cmd = [
            "docker", "exec",
            *env_args,
            self.container,
            "bash", "-c", command,
        ]
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
        except Exception as e:
            process.kill()
            await process.wait()
            logger.error("[BRIDGE][EXCEPTION] pid=%s %s", process.pid, traceback.format_exc())
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    def _extract_notebook_id(self, output: str) -> str | None:
        """从 run.py 输出中提取 NOTEBOOK_ID=<uuid>"""
        match = re.search(r"NOTEBOOK_ID=([a-f0-9-]{36})", output)
        if match:
            return match.group(1)
        # Fallback: 查找 create_notebook 打印的 "✅ Created notebook: <uuid>"
        match = re.search(r"Created notebook:\s*([a-f0-9-]{36})", output)
        if match:
            return match.group(1)
        return None

    def _parse_report(self, raw_output: str) -> str:
        """从 notebooklm ask 输出中提取分析报告"""
        # 优先用标记
        start_marker = "---REPORT_START---"
        end_marker = "---REPORT_END---"
        if start_marker in raw_output and end_marker in raw_output:
            start_idx = raw_output.index(start_marker) + len(start_marker)
            end_idx = raw_output.index(end_marker)
            return raw_output[start_idx:end_idx].strip()

        # 去掉日志/前缀行
        lines = raw_output.strip().split("\n")
        skip_prefixes = (
            "[", "DEBUG:", "INFO:", "WARN:", "ERROR:", "Traceback", "  File",
            "Using notebook:", "Notebook:", "Response:",
            "Continuing conversation", "Resumed conversation:", "Answer:",
        )
        filtered = [
            line for line in lines
            if not any(line.startswith(p) for p in skip_prefixes)
        ]
        return "\n".join(filtered).strip()

    async def run_skill(
        self,
        skill_name: str,
        stock_code: str,
        timeout: int | None = None,
    ) -> dict:
        """
        执行财报分析流水线

        Args:
            skill_name: skill 名称（目前仅支持 cninfo-financial-analysis）
            stock_code: 股票代码
            timeout: 总超时秒数，默认取配置

        Returns:
            {"success": bool, "report": str, "error": str | None}
        """
        # ===== Mock 模式 =====
        if self.mock_mode:
            await asyncio.sleep(random.uniform(3, 8))
            return {
                "success": True,
                "report": MOCK_REPORTS.get(
                    stock_code,
                    MOCK_REPORTS["default"],
                ).format(stock_code=stock_code),
                "error": None,
            }

        total_timeout = timeout or self.timeout

        # ===== Step 1: 下载财报 + 上传到 NotebookLM =====
        logger.info("[BRIDGE][STEP1] 下载+上传 | stock=%s", stock_code)
        run_cmd = (
            f"cd {self.cninfo_project} && "
            f"timeout 300 python3 scripts/run.py {stock_code}"
        )
        step1 = await self._docker_exec(
            run_cmd,
            timeout=420,
            env={"NOTEBOOKLM_HOME": self.notebooklm_dir},
        )

        if not step1["success"]:
            err = step1["stderr"] or step1["stdout"] or "run.py 执行失败"
            logger.error("[BRIDGE][STEP1_FAIL] stock=%s err=%s", stock_code, err[:500])
            return {"success": False, "report": "", "error": f"下载/上传失败: {err[:500]}"}

        # ===== Step 2: 提取 Notebook ID =====
        notebook_id = self._extract_notebook_id(step1["stdout"])
        if not notebook_id:
            logger.error("[BRIDGE][NO_NB_ID] 无法从输出提取notebook ID | stdout_tail=%s",
                         step1["stdout"][-500:])
            return {
                "success": False,
                "report": "",
                "error": "无法从 run.py 输出中提取 NotebookLM notebook ID，请检查 NotebookLM 认证",
            }
        logger.info("[BRIDGE][STEP2] notebook_id=%s", notebook_id)

        # ===== Step 3: 选择 notebook 并提问 =====
        logger.info("[BRIDGE][STEP3] AI分析 | nb=%s stock=%s", notebook_id, stock_code)
        # 用 Python -c 做 shell quoting，避免 shell 转义问题
        ask_cmd = (
            f"NOTEBOOKLM_HOME={self.notebooklm_dir} notebooklm use {notebook_id} && "
            f"NOTEBOOKLM_HOME={self.notebooklm_dir} notebooklm ask "
            f"'{ANALYSIS_PROMPT_TEMPLATE}'"
        )
        step3_timeout = max(total_timeout - 420, 120)  # 剩余时间给分析
        step3 = await self._docker_exec(
            ask_cmd,
            timeout=step3_timeout,
        )

        if not step3["success"]:
            err = step3["stderr"] or step3["stdout"] or "notebooklm ask 失败"
            logger.error("[BRIDGE][STEP3_FAIL] nb=%s err=%s", notebook_id, err[:500])
            return {
                "success": False,
                "report": "",
                "error": f"AI分析失败: {err[:500]}",
            }

        # ===== Step 4: 解析报告 =====
        report = self._parse_report(step3["stdout"])
        if not report:
            report = step3["stdout"]  # 兜底：用原始输出

        logger.info("[BRIDGE][DONE] stock=%s report_len=%d", stock_code, len(report))
        return {"success": True, "report": report, "error": None}


# 全局实例
hermes_bridge = HermesBridge()
