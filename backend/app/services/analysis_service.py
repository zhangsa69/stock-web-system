"""
分析任务服务层
"""

import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.analysis import AnalysisTask, TaskStatus
from ..config import settings

logger = logging.getLogger("stock-analysis.service")


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        stock_code: str,
        skill_name: str = "cninfo-financial-analysis",
        stock_name: str | None = None,
        user_email: str | None = None,
    ) -> AnalysisTask:
        """创建分析任务"""
        task = AnalysisTask(
            id=str(uuid.uuid4()),
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            skill_name=skill_name,
            status=TaskStatus.PENDING,
            progress=0.0,
            user_email=user_email,
        )
        self.db.add(task)
        await self.db.flush()
        logger.debug("[ANALYSIS][DB_CREATE] 任务写入数据库 | task_id=%s", task.id)
        return task

    async def get_task(self, task_id: str) -> AnalysisTask | None:
        """查询单个任务"""
        result = await self.db.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_history(self, limit: int = 50, offset: int = 0) -> list[AnalysisTask]:
        """查询分析历史"""
        result = await self.db.execute(
            select(AnalysisTask)
            .order_by(desc(AnalysisTask.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_history_count(self) -> int:
        """查询分析历史总数"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(AnalysisTask)
        )
        return result.scalar() or 0

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: float | None = None,
        report: str | None = None,
        error: str | None = None,
        celery_task_id: str | None = None,
    ):
        """更新任务状态"""
        task = await self.get_task(task_id)
        if not task:
            logger.error("[ANALYSIS][DB_UPDATE] 任务不存在 | task_id=%s", task_id)
            return
        task.status = status
        if progress is not None:
            task.progress = progress
        if report is not None:
            task.report = report
        if error is not None:
            task.error = error
        if celery_task_id is not None:
            task.celery_task_id = celery_task_id
        task.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.commit()
        logger.info(
            "[ANALYSIS][STATUS] 状态更新 | task_id=%s status=%s progress=%s",
            task_id, status.value, progress,
        )

    async def get_cached_task(self, stock_code: str, skill_name: str) -> AnalysisTask | None:
        """查找同一股票在缓存期内的已完成分析"""
        cache_days = settings.analysis_cache_days
        cutoff = datetime.utcnow() - timedelta(days=cache_days)
        result = await self.db.execute(
            select(AnalysisTask)
            .where(
                AnalysisTask.stock_code == stock_code,
                AnalysisTask.skill_name == skill_name,
                AnalysisTask.status == TaskStatus.COMPLETED,
                AnalysisTask.created_at >= cutoff,
            )
            .order_by(desc(AnalysisTask.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
