from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
from ..utils.auth import get_current_user

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/watchlist")
async def get_watchlist(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户自选股列表"""
    result = await db.execute(
        text("SELECT stock_code FROM user_watchlist WHERE user_id = :user_id ORDER BY created_at"),
        {"user_id": current_user["user_id"]}
    )
    stocks = [row[0] for row in result.fetchall()]
    return {"stocks": stocks}

@router.put("/watchlist")
async def update_watchlist(
    stocks: list[str],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户自选股列表"""
    # 删除现有记录
    await db.execute(
        text("DELETE FROM user_watchlist WHERE user_id = :user_id"),
        {"user_id": current_user["user_id"]}
    )
    # 插入新记录
    for stock_code in stocks:
        await db.execute(
            text("INSERT INTO user_watchlist (user_id, stock_code) VALUES (:user_id, :stock_code)"),
            {"user_id": current_user["user_id"], "stock_code": stock_code}
        )
    await db.commit()
    return {"success": True, "count": len(stocks)}

@router.get("/chains")
async def get_chains(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户产业链配置"""
    result = await db.execute(
        text("SELECT chain_data FROM user_chains WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 1"),
        {"user_id": current_user["user_id"]}
    )
    row = result.fetchone()
    if row:
        return {"chains": row[0]}
    return {"chains": {"custom": [], "overrides": {}}}

@router.put("/chains")
async def update_chains(
    chains: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户产业链配置"""
    import json
    # 删除现有记录
    await db.execute(
        text("DELETE FROM user_chains WHERE user_id = :user_id"),
        {"user_id": current_user["user_id"]}
    )
    # 插入新记录
    await db.execute(
        text("INSERT INTO user_chains (user_id, chain_data) VALUES (:user_id, :chain_data)"),
        {"user_id": current_user["user_id"], "chain_data": json.dumps(chains)}
    )
    await db.commit()
    return {"success": True}
