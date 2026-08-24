"""驾驶舱用户数据 API（自选股/产业链）"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.dashboard import UserDashboardData
from ..utils.auth import get_current_user

logger = logging.getLogger("stock-analysis.api.market")
router = APIRouter()

# 数据类型白名单（防止注入）
VALID_DATA_TYPES = {"watchlist", "chains"}


@router.get("/market/{data_type}")
async def get_user_data(
    data_type: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户驾驶舱数据"""
    # 参数校验
    if data_type not in VALID_DATA_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的数据类型: {data_type}")

    user_id = user["user_id"]

    stmt = select(UserDashboardData).where(
        UserDashboardData.user_id == user_id,
        UserDashboardData.data_type == data_type,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        # 返回空数据（前端会使用默认值）
        return {"data_type": data_type, "data_value": [] if data_type == "watchlist" else {}}

    return {"data_type": data_type, "data_value": record.data_value}


@router.put("/market/{data_type}")
async def save_user_data(
    data_type: str,
    data_value: dict | list,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """保存用户驾驶舱数据"""
    # 参数校验
    if data_type not in VALID_DATA_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的数据类型: {data_type}")

    # 数据类型校验
    if data_type == "watchlist" and not isinstance(data_value, list):
        raise HTTPException(status_code=400, detail="自选股数据必须是数组")
    if data_type == "chains" and not isinstance(data_value, dict):
        raise HTTPException(status_code=400, detail="产业链数据必须是对象")

    user_id = user["user_id"]

    # UPSERT 逻辑
    stmt = select(UserDashboardData).where(
        UserDashboardData.user_id == user_id,
        UserDashboardData.data_type == data_type,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record:
        # 更新现有记录
        record.data_value = data_value
        logger.info("更新用户数据 | user_id=%s data_type=%s", user_id, data_type)
    else:
        # 创建新记录
        record = UserDashboardData(
            user_id=user_id,
            data_type=data_type,
            data_value=data_value,
        )
        db.add(record)
        logger.info("创建用户数据 | user_id=%s data_type=%s", user_id, data_type)

    await db.flush()
    return {"success": True, "data_type": data_type}


@router.delete("/market/{data_type}")
async def delete_user_data(
    data_type: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除用户驾驶舱数据"""
    if data_type not in VALID_DATA_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的数据类型: {data_type}")

    user_id = user["user_id"]

    stmt = select(UserDashboardData).where(
        UserDashboardData.user_id == user_id,
        UserDashboardData.data_type == data_type,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if record:
        await db.delete(record)
        await db.flush()
        logger.info("删除用户数据 | user_id=%s data_type=%s", user_id, data_type)

    return {"success": True}
