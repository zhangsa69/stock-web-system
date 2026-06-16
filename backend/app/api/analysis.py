"""
分析 API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
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
from ..models.user import User
from ..utils.auth import get_current_user, get_optional_user

logger = logging.getLogger("stock-analysis.api")
router = APIRouter()


@router.post("/analysis/start", response_model=AnalysisResponse)
async def start_analysis(
    req: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """提交股票分析任务"""
    email = user["email"]
    logger.info(
        "[ANALYSIS][START] 收到分析请求 | stock_code=%s skill=%s user=%s",
        req.stock_code, req.skill_name, email,
    )
    service = AnalysisService(db)

    # ── 查询用户点券余额 ──
    user_stmt = select(User).where(User.email == email)
    user_result = await db.execute(user_stmt)
    u = user_result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    if u.tickets <= 0:
        raise HTTPException(status_code=402, detail="点券余额不足，请先充值（每次分析消耗 1 点券）")

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
        user_email=email,
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

    # ── 扣除 1 点券 ──
    u.tickets -= 1
    await db.flush()
    logger.info("[ANALYSIS][DEDUCT] 扣除点券 | user=%s balance=%d", email, u.tickets)

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


@router.get("/analysis/{task_id}/download")
async def download_report(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """下载原始 Markdown 报告"""
    service = AnalysisService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="分析尚未完成")
    if not task.report:
        raise HTTPException(status_code=404, detail="报告内容为空")

    filename = f"{task.stock_code}_{task.stock_name or task.stock_code}_分析报告.md"
    return Response(
        content=task.report.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
