"""
发送分析结果邮件（同步方式，避免 event loop 冲突）
"""
import logging
import traceback
from .celery_app import celery_app
from ..services.email_service import email_service
from ..database import engine
from ..models.analysis import AnalysisTask

logger = logging.getLogger("stock-analysis.email_task")


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def send_analysis_email(self, task_id: str):
    """分析完成后发送结果邮件（同步 DB 查询 + 同步 SMTP）"""
    logger.info(
        "[EMAIL_SEND][TASK_START] Celery邮件任务启动 | task_id=%s celery_id=%s",
        task_id, self.request.id,
    )

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from ..config import settings

        sync_url = settings.database_url_sync
        sync_engine = create_engine(sync_url, pool_pre_ping=True)
        SyncSession = sessionmaker(bind=sync_engine)

        with SyncSession() as db:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

            if not task:
                logger.error("[EMAIL_SEND][TASK_NOT_FOUND] task_id=%s", task_id)
                return

            if not task.user_email:
                logger.warning("[EMAIL_SEND][NO_EMAIL] task_id=%s", task_id)
                return

            if not task.report:
                logger.warning("[EMAIL_SEND][NO_REPORT] task_id=%s", task_id)
                return

            logger.info(
                "[EMAIL_SEND][SENDING] to=%s stock=%s report_len=%d",
                task.user_email, task.stock_code, len(task.report),
            )

            email_service.send_report_email(
                to_email=task.user_email,
                stock_code=task.stock_code,
                stock_name=task.stock_name or task.stock_code,
                report=task.report,
            )
            logger.info("[EMAIL_SEND][SUCCESS] task_id=%s", task_id)

        sync_engine.dispose()

    except Exception as e:
        logger.error(
            "[EMAIL_SEND][FAILED] task_id=%s reason=%s traceback=%s",
            task_id, str(e), traceback.format_exc(),
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            logger.error("[EMAIL_SEND][MAX_RETRIES] task_id=%s", task_id)

    logger.info("[EMAIL_SEND][TASK_END] task_id=%s", task_id)
