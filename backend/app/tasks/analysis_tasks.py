"""
Celery 异步分析任务（同步 DB 版本，避免 asyncpg event loop 冲突）
"""
import asyncio
import logging
import traceback
from .celery_app import celery_app
from ..services.hermes_bridge import hermes_bridge
from ..config import settings
from ..models.analysis import AnalysisTask, TaskStatus

logger = logging.getLogger("stock-analysis.tasks")


def _get_sync_db():
    """创建同步数据库会话（Celery worker 中用，避免 event loop 冲突）"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sync_engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    SyncSession = sessionmaker(bind=sync_engine)
    return SyncSession(), sync_engine


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_hermes_skill(self, task_id: str, skill_name: str, stock_code: str):
    """执行 Hermes skill 分析任务（两步：分析 → HTML）"""
    logger.info(
        "[ANALYSIS][STEP_START] Celery任务开始执行 | task_id=%s skill=%s stock=%s",
        task_id, skill_name, stock_code,
    )

    db, sync_engine = _get_sync_db()
    try:
        # 更新为运行中
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            logger.error("[ANALYSIS][TASK_NOT_FOUND] task_id=%s", task_id)
            return

        task.status = TaskStatus.RUNNING
        task.progress = 0.1
        task.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()

        logger.info(
            "[ANALYSIS][HERMES_CALL] 开始调用 Hermes | task_id=%s skill=%s stock=%s",
            task_id, skill_name, stock_code,
        )

        # 调用 Hermes Bridge（异步）
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                hermes_bridge.run_skill(
                    skill_name=skill_name,
                    stock_code=stock_code,
                )
            )
        except Exception as e:
            logger.error(
                "[ANALYSIS][HERMES_EXCEPTION] Hermes调用崩溃 | task_id=%s exception=%s traceback=%s",
                task_id, str(e), traceback.format_exc(),
            )
            result = {"success": False, "report": "", "html_report": "", "error": f"Hermes调用崩溃: {str(e)}"}
        finally:
            loop.close()

        # 刷新 task（可能已被其他进程修改）
        db.refresh(task)

        if result["success"]:
            report_len = len(result.get("report", ""))
            html_len = len(result.get("html_report", ""))
            logger.info(
                "[ANALYSIS][SUCCESS] 分析成功 | task_id=%s report=%d html=%d",
                task_id, report_len, html_len,
            )
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.report = result["report"]
            task.html_report = result.get("html_report", "")
            task.updated_at = __import__("datetime").datetime.utcnow()
            db.commit()

            # 异步发送邮件
            try:
                from .email_tasks import send_analysis_email
                send_analysis_email.delay(task_id)
                logger.info(
                    "[ANALYSIS][EMAIL_TRIGGER] 邮件任务已触发 | task_id=%s", task_id,
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
            task.status = TaskStatus.FAILED
            task.progress = 1.0
            task.error = error_msg
            task.updated_at = __import__("datetime").datetime.utcnow()
            db.commit()

    except Exception as e:
        logger.error(
            "[ANALYSIS][CRASH] 分析任务崩溃 | task_id=%s reason=%s traceback=%s",
            task_id, str(e), traceback.format_exc(),
        )
        try:
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.updated_at = __import__("datetime").datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        sync_engine.dispose()

    logger.info("[ANALYSIS][STEP_END] Celery任务结束 | task_id=%s", task_id)
