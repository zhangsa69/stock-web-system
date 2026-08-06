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


@celery_app.task(bind=True, max_retries=6, default_retry_delay=60)
def run_hermes_skill(self, task_id: str, skill_name: str, stock_code: str):
    """执行 Hermes skill 分析任务（指数退避重试，最多6次）"""
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

            # 异步发送邮件 —— 已禁用（2026-06-17 用户要求取消邮件通知）
            # 异步发送邮件
            # try:
            # from .email_tasks import send_analysis_email
            # send_analysis_email.delay(task_id)
            # logger.info(
            # "[ANALYSIS][EMAIL_TRIGGER] 邮件任务已触发 | task_id=%s", task_id,
            # )
            # except Exception as e:
            # logger.error(
            # "[ANALYSIS][EMAIL_TRIGGER_FAIL] 邮件任务触发失败 | task_id=%s reason=%s",
            # task_id, str(e), exc_info=True,
#                 )
        else:
            error_msg = result.get("error", "未知错误")
            logger.error(
                "[ANALYSIS][FAILED] 分析失败 | task_id=%s reason=%s",
                task_id, error_msg,
            )

            # ── 判断是否可重试的错误（并发塞车 / 网络抖动）──
            _TRANSIENT_KW = (
                "503", "Server busy", "连接失败", "重试",
                "超时", "Timeout", "ConnectError", "ConnectionError",
                "RemoteDisconnected", "崩溃",
            )
            is_transient = any(kw in error_msg for kw in _TRANSIENT_KW)

            if is_transient and self.request.retries < self.max_retries:
                from celery.exceptions import Retry
                countdown = 60 * (self.request.retries + 1)  # 60, 120, 180, 240, 300, 360s（线性，总覆盖21min）
                logger.warning(
                    "[ANALYSIS][RETRY_SCHEDULED] 临时故障，指数退避重试 | task_id=%s attempt=%d/%d countdown=%ds",
                    task_id, self.request.retries + 1, self.max_retries, countdown,
                )
                # 不设FAILED状态，保持RUNNING让前端知道还在队列中
                raise self.retry(countdown=countdown)

            # ── 不可重试 or 重试耗尽 → 标记失败 + 退点券 ──
            logger.error(
                "[ANALYSIS][FINAL_FAIL] 分析最终失败（重试%d次后）| task_id=%s reason=%s",
                self.request.retries, task_id, error_msg,
            )
            task.status = TaskStatus.FAILED
            task.progress = 1.0
            task.error = error_msg
            task.updated_at = __import__("datetime").datetime.utcnow()
            db.commit()

            # 退点券
            try:
                from ..models.user import User
                if task.user_email:
                    user = db.query(User).filter(User.email == task.user_email).first()
                    if user:
                        before = user.tickets
                        user.tickets += 2
                        db.commit()
                        logger.info(
                            "[ANALYSIS][REFUND] 分析失败退还点券 | task_id=%s user=%s %d→%d",
                            task_id, task.user_email, before, user.tickets,
                        )
            except Exception as refund_err:
                logger.error("[ANALYSIS][REFUND_FAIL] 退还点券失败 | task_id=%s %s", task_id, str(refund_err))

    except Exception as e:
        from celery.exceptions import Retry
        if isinstance(e, Retry):
            raise  # 不要拦截——让 Celery 处理重试

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

                # 崩溃也退点券
                try:
                    from ..models.user import User
                    if task.user_email:
                        user = db.query(User).filter(User.email == task.user_email).first()
                        if user:
                            before = user.tickets
                            user.tickets += 2
                            db.commit()
                            logger.info(
                                "[ANALYSIS][REFUND_CRASH] 崩溃退还点券 | task_id=%s user=%s %d→%d",
                                task_id, task.user_email, before, user.tickets,
                            )
                except Exception:
                    pass
        except Exception:
            pass
    finally:
        db.close()
        sync_engine.dispose()

    logger.info("[ANALYSIS][STEP_END] Celery任务结束 | task_id=%s", task_id)
