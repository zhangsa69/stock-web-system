"""
Hermes CLI 桥接层

通过 subprocess 调用 Hermes Agent CLI，不修改 Hermes 源码。
每个调用分配独立 session，支持超时控制和输出解析。
支持 Mock 模式用于本地开发调试。
"""

import asyncio
import os
import random
import shutil
import tempfile
from pathlib import Path
from ..config import settings

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


class HermesBridge:
    """通过 CLI 子进程调用 Hermes skill"""

    def __init__(self):
        self.hermes_bin = settings.hermes_bin
        self.hermes_home = settings.hermes_home
        self.timeout = settings.hermes_timeout
        self.mock_mode = settings.hermes_mock

    async def run_skill(
        self,
        skill_name: str,
        stock_code: str,
        timeout: int | None = None,
    ) -> dict:
        """
        调用 Hermes skill 分析股票

        Args:
            skill_name: skill 名称，如 "cninfo-financial-analysis"
            stock_code: 股票代码，如 "600519"
            timeout: 超时秒数，默认取配置

        Returns:
            {"success": bool, "report": str, "error": str | None}
        """
        # ===== Mock 模式：本地开发无需真实 Hermes =====
        if self.mock_mode:
            await asyncio.sleep(random.uniform(3, 8))  # 模拟分析耗时
            return {
                "success": True,
                "report": MOCK_REPORTS.get(
                    stock_code,
                    MOCK_REPORTS["default"].format(stock_code=stock_code),
                ).format(stock_code=stock_code),
                "error": None,
            }

        # ===== 真实模式：通过 subprocess 调用 Hermes CLI =====
        timeout = timeout or self.timeout
        session_dir = tempfile.mkdtemp(prefix="hermes_session_")

        env = {
            **os.environ,
            "HERMES_HOME": self.hermes_home,
            "HERMES_SESSION_DIR": session_dir,
        }

        cmd = [self.hermes_bin, "skill", skill_name, "--code", stock_code]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            if process.returncode != 0:
                return {
                    "success": False,
                    "report": "",
                    "error": f"Hermes 返回非零退出码 {process.returncode}: {stderr_text[:500]}",
                }

            report = self._parse_report(stdout_text)
            if not report:
                report = stdout_text

            return {"success": True, "report": report, "error": None}

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "success": False,
                "report": "",
                "error": f"Hermes 分析超时（{self.timeout}秒）",
            }

        except Exception as e:
            process.kill()
            await process.wait()
            return {
                "success": False,
                "report": "",
                "error": f"Hermes 调用异常: {str(e)}",
            }

        finally:
            shutil.rmtree(session_dir, ignore_errors=True)

    def _parse_report(self, raw_output: str) -> str:
        """从 Hermes 输出中提取分析报告。

        支持两种方式：
        1. 如果有 ---REPORT_START--- / ---REPORT_END--- 标记，提取中间内容
        2. 否则返回全部输出
        """
        start_marker = "---REPORT_START---"
        end_marker = "---REPORT_END---"

        if start_marker in raw_output and end_marker in raw_output:
            start_idx = raw_output.index(start_marker) + len(start_marker)
            end_idx = raw_output.index(end_marker)
            return raw_output[start_idx:end_idx].strip()

        # 如果没有标记，尝试去掉常见的控制台前缀行
        lines = raw_output.strip().split("\n")
        # 去掉非报告内容行（以常见日志前缀开头的行）
        filtered = [
            line for line in lines
            if not any(
                line.startswith(prefix)
                for prefix in ["[", "DEBUG:", "INFO:", "WARN:", "ERROR:", "Traceback", "  File"]
            )
        ]
        return "\n".join(filtered).strip()


# 全局实例
hermes_bridge = HermesBridge()
