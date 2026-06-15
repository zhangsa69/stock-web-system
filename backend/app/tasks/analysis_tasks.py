"""
Celery 异步分析任务
"""

import asyncio
from .celery_app import celery_app
from ..services.hermes_bridge import hermes_bridge
from ..services.analysis_service import AnalysisService
from ..models.analysis import TaskStatus
from ..database import async_session


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
            result = await hermes_bridge.run_skill(
                skill_name=skill_name,
                stock_code=stock_code,
            )

            if result["success"]:
                await service.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    progress=1.0,
                    report=result["report"],
                )
            else:
                await service.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    progress=1.0,
                    error=result["error"],
                )

    result = _run_async(_execute())
    return result
