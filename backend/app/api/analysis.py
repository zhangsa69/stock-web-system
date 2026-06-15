"""
分析 API 路由
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisHistoryItem,
)
from ..services.analysis_service import AnalysisService
from ..models.analysis import TaskStatus

logger = logging.getLogger("stock-analysis.api")
router = APIRouter()


@router.post("/analysis/start", response_model=AnalysisResponse)
async def start_analysis(
    req: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """提交股票分析任务"""
    logger.info(
        "[ANALYSIS][START] 收到分析请求 | stock_code=%s skill=%s email=%s",
        req.stock_code, req.skill_name, req.email,
    )
    service = AnalysisService(db)

    # 检查缓存
    cached = await service.get_cached_task(req.stock_code, req.skill_name)
    if cached:
        logger.info(
            "[ANALYSIS][CACHE_HIT] 命中缓存 | task_id=%s stock_code=%s",
            cached.id, req.stock_code,
        )
        return AnalysisResponse(
            task_id=cached.id,
            status="completed",
            estimated_seconds=0,
        )

    # 创建任务
    task = await service.create_task(
        stock_code=req.stock_code,
        skill_name=req.skill_name,
        user_email=req.email,
    )
    logger.info(
        "[ANALYSIS][TASK_CREATED] 任务已创建 | task_id=%s stock_code=%s",
        task.id, req.stock_code,
    )

    # 提交 Celery 异步任务
    try:
        from ..tasks.analysis_tasks import run_hermes_skill
        celery_task = run_hermes_skill.delay(
            task_id=task.id,
            skill_name=req.skill_name,
            stock_code=req.stock_code,
        )
        logger.info(
            "[ANALYSIS][CELERY_SUBMIT] Celery任务已提交 | task_id=%s celery_id=%s",
            task.id, celery_task.id,
        )
    except Exception as e:
        logger.error(
            "[ANALYSIS][CELERY_FAIL] Celery提交失败 | task_id=%s reason=%s",
            task.id, str(e), exc_info=True,
        )
        await service.update_task_status(
            task_id=task.id,
            status=TaskStatus.FAILED,
            error=f"任务调度失败: {str(e)}",
        )
        raise HTTPException(status_code=500, detail="分析任务调度失败，请稍后重试")

    await service.update_task_status(
        task_id=task.id,
        status=TaskStatus.PENDING,
        celery_task_id=celery_task.id,
    )

    return AnalysisResponse(
        task_id=task.id,
        status="pending",
        estimated_seconds=600,
    )


@router.get("/analysis/{task_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """查询分析任务状态"""
    service = AnalysisService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return AnalysisStatusResponse(
        task_id=task.id,
        stock_code=task.stock_code,
        stock_name=task.stock_name,
        status=task.status.value,
        progress=task.progress,
        report=task.report,
        html_report=task.html_report,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/analysis/history")
async def get_analysis_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取分析历史列表"""
    service = AnalysisService(db)
    total = await service.get_history_count()
    items = await service.get_history(
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            AnalysisHistoryItem(
                task_id=item.id,
                stock_code=item.stock_code,
                stock_name=item.stock_name,
                status=item.status.value,
                created_at=item.created_at,
            )
            for item in items
        ],
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
