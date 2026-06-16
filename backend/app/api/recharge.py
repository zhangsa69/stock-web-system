"""充值核销 API"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.recharge import RechargeCode
from ..models.user import User
from ..schemas.recharge import RedeemRequest, RedeemResponse, BalanceResponse
from ..utils.auth import get_current_user

logger = logging.getLogger("stock-analysis.api.recharge")
router = APIRouter(prefix="/recharge", tags=["recharge"])


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_code(
    req: RedeemRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """核销充值卡密"""
    code = req.code.strip()
    email = user["email"]

    # 找卡密
    stmt = select(RechargeCode).where(RechargeCode.code == code)
    result = await db.execute(stmt)
    rc = result.scalar_one_or_none()

    if not rc:
        logger.warning("[RECHARGE] 无效卡密 | email=%s code=%s", email, code[:8])
        raise HTTPException(status_code=400, detail="无效的充值卡密，请确认后重试")

    if rc.is_used:
        logger.warning("[RECHARGE] 卡密已被使用 | email=%s code=%s used_by=%s",
                       email, code[:8], rc.used_by)
        raise HTTPException(status_code=400, detail="该充值卡密已被使用")

    # 找用户
    user_stmt = select(User).where(User.email == email)
    user_result = await db.execute(user_stmt)
    u = user_result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 核销
    rc.is_used = True
    rc.used_by = email
    rc.used_at = datetime.now(timezone.utc)

    u.tickets += rc.ticket_value

    await db.flush()
    await db.commit()

    logger.info("[RECHARGE] 充值成功 | email=%s value=%d balance=%d",
                email, rc.ticket_value, u.tickets)

    return RedeemResponse(
        success=True,
        message=f"充值成功！获得 {rc.ticket_value} 点券",
        tickets_added=rc.ticket_value,
        balance=u.tickets,
    )


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户点券余额"""
    email = user["email"]
    user_stmt = select(User).where(User.email == email)
    result = await db.execute(user_stmt)
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    return BalanceResponse(tickets=u.tickets, email=u.email)
