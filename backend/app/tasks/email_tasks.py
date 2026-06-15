"""
发送分析结果邮件（独立 Celery 任务，不影响主分析流程）
"""
import logging
import traceback
from .celery_app import celery_app
from .analysis_tasks import _run_async
from ..services.email_service import email_service
from ..services.analysis_service import AnalysisService
from ..database import async_session

logger = logging.getLogger("stock-analysis.email_task")


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def send_analysis_email(self, task_id: str):
    """分析完成后发送结果邮件"""
    logger.info(
        "[EMAIL_SEND][TASK_START] Celery邮件任务启动 | task_id=%s celery_id=%s",
        task_id, self.request.id,
    )

    async def _get_and_send():
        async with async_session() as db:
            service = AnalysisService(db)
            task = await service.get_task(task_id)

            # 检查必要数据
            if not task:
                logger.error(
                    "[EMAIL_SEND][TASK_NOT_FOUND] 任务不存在，无法发送邮件 | task_id=%s",
                    task_id,
                )
                return

            if not task.user_email:
                logger.warning(
                    "[EMAIL_SEND][NO_EMAIL] 任务未绑定邮箱 | task_id=%s stock=%s",
                    task_id, task.stock_code,
                )
                return

            if not task.report:
                logger.warning(
                    "[EMAIL_SEND][NO_REPORT] 任务无报告内容 | task_id=%s stock=%s",
                    task_id, task.stock_code,
                )
                return

            logger.info(
                "[EMAIL_SEND][SENDING] 准备发送邮件 | task_id=%s to=%s stock=%s report_len=%d",
                task_id, task.user_email, task.stock_code, len(task.report),
            )

            try:
                email_service.send_report_email(
                    to_email=task.user_email,
                    stock_code=task.stock_code,
                    stock_name=task.stock_name or task.stock_code,
                    report=task.report,
                )
                logger.info(
                    "[EMAIL_SEND][TASK_SUCCESS] 邮件任务完成 | task_id=%s",
                    task_id,
                )
            except Exception as e:
                logger.error(
                    "[EMAIL_SEND][TASK_FAILED] 邮件发送失败 | task_id=%s reason=%s traceback=%s",
                    task_id, str(e), traceback.format_exc(),
                )
                # 根据重试次数决定是否再次尝试
                if self.request.retries < self.max_retries:
                    logger.info(
                        "[EMAIL_SEND][RETRY] 将在60秒后重试 | task_id=%s retry=%d/%d",
                        task_id, self.request.retries + 1, self.max_retries,
                    )
                    raise self.retry(exc=e)
                else:
                    logger.error(
                        "[EMAIL_SEND][MAX_RETRIES] 已达最大重试次数，放弃发送 | task_id=%s",
                        task_id,
                    )

    _run_async(_get_and_send())
    logger.info("[EMAIL_SEND][TASK_END] Celery邮件任务结束 | task_id=%s", task_id)
