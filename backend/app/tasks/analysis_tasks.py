"""
Celery 异步分析任务
"""

import asyncio
import logging
import traceback
from .celery_app import celery_app
from ..services.hermes_bridge import hermes_bridge
from ..services.analysis_service import AnalysisService
from ..models.analysis import TaskStatus
from ..database import async_session

logger = logging.getLogger("stock-analysis.tasks")


def _run_async(coro):
    """在同步任务中运行异步协程"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_hermes_skill(self, task_id: str, skill_name: str, stock_code: str):
    """执行 Hermes skill 分析任务"""
    logger.info(
        "[ANALYSIS][STEP_START] Celery任务开始执行 | task_id=%s skill=%s stock=%s",
        task_id, skill_name, stock_code,
    )

    async def _execute():
        async with async_session() as db:
            service = AnalysisService(db)

            # 更新为运行中
            await service.update_task_status(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                progress=0.1,
            )

            # 调用 Hermes
            try:
                logger.info(
                    "[ANALYSIS][HERMES_CALL] 开始调用 Hermes | task_id=%s skill=%s stock=%s",
                    task_id, skill_name, stock_code,
                )
                result = await hermes_bridge.run_skill(
                    skill_name=skill_name,
                    stock_code=stock_code,
                )
            except Exception as e:
                logger.error(
                    "[ANALYSIS][HERMES_EXCEPTION] Hermes调用崩溃 | task_id=%s exception=%s traceback=%s",
                    task_id, str(e), traceback.format_exc(),
                )
                result = {"success": False, "report": "", "error": f"Hermes调用崩溃: {str(e)}"}

            if result["success"]:
                report_len = len(result.get("report", ""))
                logger.info(
                    "[ANALYSIS][SUCCESS] 分析成功 | task_id=%s report_length=%d",
                    task_id, report_len,
                )
                await service.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    progress=1.0,
                    report=result["report"],
                )
                # 分析完成后异步发送邮件
                try:
                    from .email_tasks import send_analysis_email
                    send_analysis_email.delay(task_id)
                    logger.info(
                        "[ANALYSIS][EMAIL_TRIGGER] 邮件任务已触发 | task_id=%s",
                        task_id,
                    )
                except Exception as e:
                    logger.error(
                        "[ANALYSIS][EMAIL_TRIGGER_FAIL] 邮件任务触发失败 | task_id=%s reason=%s",
                        task_id, str(e), exc_info=True,
                    )
            else:
                error_msg = result.get("error", "未知错误")
                logger.error(
                    "[ANALYSIS][FAILED] 分析失败 | task_id=%s reason=%s",
                    task_id, error_msg,
                )
                await service.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    progress=1.0,
                    error=error_msg,
                )

    result = _run_async(_execute())
    logger.info(
        "[ANALYSIS][STEP_END] Celery任务结束 | task_id=%s success=%s",
        task_id,
        result.get("success") if isinstance(result, dict) else "unknown",
    )
    return result
