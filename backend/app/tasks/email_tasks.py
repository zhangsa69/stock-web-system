"""
发送分析结果邮件（独立 Celery 任务，不影响主分析流程）
"""
import logging
from .celery_app import celery_app
from .analysis_tasks import _run_async
from ..services.email_service import email_service
from ..services.analysis_service import AnalysisService
from ..database import async_session

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def send_analysis_email(self, task_id: str):
    """分析完成后发送结果邮件"""

    async def _get_and_send():
        async with async_session() as db:
            service = AnalysisService(db)
            task = await service.get_task(task_id)
            if not task or not task.user_email or not task.report:
                logger.warning(f"跳过邮件发送: task={task_id} 缺少必要数据")
                return

            email_service.send_report_email(
                to_email=task.user_email,
                stock_code=task.stock_code,
                stock_name=task.stock_name or task.stock_code,
                report=task.report,
            )

    _run_async(_get_and_send())
