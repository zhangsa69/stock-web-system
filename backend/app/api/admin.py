"""管理后台 API"""
import logging
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..models.analysis import AnalysisTask, TaskStatus
from ..models.recharge import RechargeCode
from ..services.auth_service import (
    AuthService, generate_verification_code, create_access_token,
)
from ..services.email_service import EmailService
from ..utils.auth import get_current_admin

logger = logging.getLogger("stock-analysis.api.admin")
router = APIRouter(prefix="/admin", tags=["admin"])


# ── Schemas ──

class AdminSendCodeRequest(BaseModel):
    email: str

class AdminLoginRequest(BaseModel):
    email: str
    code: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DashboardStats(BaseModel):
    total_users: int
    total_codes: int
    used_codes: int
    unused_codes: int
    total_analyses: int
    completed_analyses: int
    failed_analyses: int
    total_tickets_sold: int
    total_tickets_used: int

class CodeItem(BaseModel):
    id: str
    code: str
    ticket_value: int
    is_used: bool
    used_by: str | None
    used_at: str | None
    created_at: str

class CodeListResponse(BaseModel):
    total: int
    items: list[CodeItem]

class DeleteCodesRequest(BaseModel):
    ids: list[str]

class DeleteCodesResponse(BaseModel):
    deleted: int
    message: str

class UserItem(BaseModel):
    id: str
    email: str
    tickets: int
    is_verified: bool
    created_at: str

class UserListResponse(BaseModel):
    total: int
    items: list[UserItem]

class AdjustTicketsRequest(BaseModel):
    amount: int  # 正数=增加，负数=减少

class ImportResult(BaseModel):
    imported: int
    skipped: int
    message: str


# ── Auth (验证码登录，无密码) ──
# Redis 存储验证码（跨 worker 共享）
ADMIN_CODE_PREFIX = "admin:code:"
ADMIN_RATE_PREFIX = "admin:rate:"


async def _get_redis():
    return aioredis.from_url(settings.redis_url, decode_responses=True)


@router.post("/send-code")
async def admin_send_code(req: AdminSendCodeRequest):
    """向管理员邮箱发送验证码"""
    email = req.email.strip().lower()
    admin_emails = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
    if email not in admin_emails:
        raise HTTPException(status_code=403, detail="非管理员邮箱")

    redis = await _get_redis()

    # 速率限制：60秒内只能发一次
    rate_key = f"{ADMIN_RATE_PREFIX}{email}"
    if await redis.exists(rate_key):
        await redis.close()
        raise HTTPException(status_code=429, detail="请60秒后再试")

    code = generate_verification_code()

    # 存验证码到 Redis，10分钟过期
    code_key = f"{ADMIN_CODE_PREFIX}{email}"
    await redis.setex(code_key, 600, code)
    await redis.setex(rate_key, 60, "1")
    await redis.close()

    try:
        await EmailService.send_verification_code(email, code)
    except Exception as e:
        logger.error("管理员验证码发送失败: %s", str(e))
        raise HTTPException(status_code=500, detail="验证码发送失败")

    return {"message": f"验证码已发送至 {email}，10分钟内有效"}


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest):
    """验证码登录，返回 JWT"""
    email = req.email.strip().lower()
    code = req.code.strip()

    admin_emails = [e.strip() for e in settings.admin_emails.split(",") if e.strip()]
    if email not in admin_emails:
        raise HTTPException(status_code=403, detail="非管理员邮箱")

    redis = await _get_redis()
    code_key = f"{ADMIN_CODE_PREFIX}{email}"
    stored_code = await redis.get(code_key)

    if not stored_code:
        await redis.close()
        raise HTTPException(status_code=400, detail="验证码已过期或未发送，请重新发送")

    if stored_code != code:
        await redis.close()
        raise HTTPException(status_code=400, detail="验证码错误")

    # 验证成功，删除验证码
    await redis.delete(code_key)
    await redis.close()

    # 确保管理员用户存在于数据库中（无密码）
    # 复用现有 User 模型
    from ..models.user import User
    from ..database import async_session

    async with async_session() as db:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        u = result.scalar_one_or_none()
        if not u:
            u = User(email=email, hashed_password="", is_verified=True)
            db.add(u)
            await db.flush()
            await db.commit()
            user_id = u.id
        else:
            user_id = u.id

    token = create_access_token(user_id, email)
    logger.info("管理员登录: %s", email)
    return AdminLoginResponse(access_token=token)


# ── Dashboard ──

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(admin: dict = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    """管理后台首页统计"""
    # 用户数
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0

    # 卡密统计
    total_codes = (await db.execute(select(func.count()).select_from(RechargeCode))).scalar() or 0
    used_codes = (await db.execute(
        select(func.count()).where(RechargeCode.is_used == True)
    )).scalar() or 0

    # 分析统计
    total_analyses = (await db.execute(select(func.count()).select_from(AnalysisTask))).scalar() or 0
    completed = (await db.execute(
        select(func.count()).where(AnalysisTask.status == TaskStatus.COMPLETED)
    )).scalar() or 0
    failed = (await db.execute(
        select(func.count()).where(AnalysisTask.status == TaskStatus.FAILED)
    )).scalar() or 0

    # 点券统计
    total_sold = (await db.execute(
        select(func.coalesce(func.sum(RechargeCode.ticket_value), 0)).where(RechargeCode.is_used == True)
    )).scalar() or 0

    total_used = (await db.execute(
        select(func.coalesce(func.sum(User.tickets), 0))
    )).scalar() or 0
    # 总消耗 = 总售出 - 当前剩余
    total_consumed = total_sold - total_used
    if total_consumed < 0:
        total_consumed = 0

    return DashboardStats(
        total_users=total_users,
        total_codes=total_codes,
        used_codes=used_codes,
        unused_codes=total_codes - used_codes,
        total_analyses=total_analyses,
        completed_analyses=completed,
        failed_analyses=failed,
        total_tickets_sold=total_sold,
        total_tickets_used=total_consumed,
    )


# ── 卡密管理 ──

@router.get("/codes", response_model=CodeListResponse)
async def list_codes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str = Query("", description="搜索卡密"),
    used_filter: str = Query("all", description="all/used/unused"),
    ticket_value: int = Query(0, description="按面值筛选，0=全部"),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """卡密列表"""
    q = select(RechargeCode)

    if used_filter == "used":
        q = q.where(RechargeCode.is_used == True)
    elif used_filter == "unused":
        q = q.where(RechargeCode.is_used == False)

    if ticket_value > 0:
        q = q.where(RechargeCode.ticket_value == ticket_value)

    if search:
        q = q.where(RechargeCode.code.ilike(f"%{search}%"))

    # 总数
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # 分页
    q = q.order_by(desc(RechargeCode.created_at)).limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(q)
    codes = result.scalars().all()

    return CodeListResponse(
        total=total,
        items=[
            CodeItem(
                id=c.id,
                code=c.code,
                ticket_value=c.ticket_value,
                is_used=c.is_used,
                used_by=c.used_by,
                used_at=c.used_at.isoformat() if c.used_at else None,
                created_at=c.created_at.isoformat(),
            )
            for c in codes
        ],
    )


@router.post("/codes/import", response_model=ImportResult)
async def import_codes(
    file: UploadFile = File(...),
    ticket_value: int = Query(..., description="点券面值: 1 或 20"),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """导入卡密 CSV（每行一个卡密）"""
    import uuid

    if ticket_value not in (2, 30, 50, 100):
        raise HTTPException(status_code=400, detail="ticket_value 只能是 2 / 30 / 50 / 100")

    content = (await file.read()).decode("utf-8", errors="replace")
    # 解析每一行：去掉首尾空白/逗号/引号；支持 CSV 格式（取第一列）
    raw_lines = [l.strip() for l in content.split("\n")]
    lines = []
    for l in raw_lines:
        if not l:
            continue
        # 如果是 CSV 格式（含逗号），取第一列
        code = l.split(",")[0]
        # 去掉首尾空白、引号、逗号
        code = code.strip().strip('"').strip("'").strip(",").strip()
        if code:
            lines.append(code)

    imported = 0
    skipped = 0

    for code in lines:
        # 检查是否已存在
        existing = await db.execute(
            select(RechargeCode).where(RechargeCode.code == code)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        rc = RechargeCode(
            id=str(uuid.uuid4()),
            code=code,
            ticket_value=ticket_value,
        )
        db.add(rc)
        imported += 1

    await db.flush()
    await db.commit()

    logger.info("[ADMIN] 导入卡密 | value=%d imported=%d skipped=%d", ticket_value, imported, skipped)
    return ImportResult(
        imported=imported,
        skipped=skipped,
        message=f"成功导入 {imported} 条，跳过 {skipped} 条（已存在）",
    )


@router.delete("/codes", response_model=DeleteCodesResponse)
async def delete_codes(
    req: DeleteCodesRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """批量删除卡密"""
    if not req.ids:
        raise HTTPException(status_code=400, detail="请提供要删除的卡密 ID")

    # 只删除未使用的卡密，防止误删已核销的
    stmt = select(RechargeCode).where(
        RechargeCode.id.in_(req.ids),
        RechargeCode.is_used == False,
    )
    result = await db.execute(stmt)
    codes = result.scalars().all()

    for c in codes:
        await db.delete(c)

    await db.commit()

    skipped = len(req.ids) - len(codes)
    msg = f"成功删除 {len(codes)} 条"
    if skipped > 0:
        msg += f"，跳过 {skipped} 条（已使用不可删除）"

    logger.info("[ADMIN] 批量删除卡密 | total=%d deleted=%d skipped=%d", len(req.ids), len(codes), skipped)
    return DeleteCodesResponse(deleted=len(codes), message=msg)


# ── 用户管理 ──

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str = Query("", description="搜索邮箱"),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """用户列表"""
    q = select(User)
    if search:
        q = q.where(User.email.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    q = q.order_by(desc(User.created_at)).limit(page_size).offset((page - 1) * page_size)
    result = await db.execute(q)
    users = result.scalars().all()

    return UserListResponse(
        total=total,
        items=[
            UserItem(
                id=u.id,
                email=u.email,
                tickets=u.tickets,
                is_verified=u.is_verified,
                created_at=u.created_at.isoformat(),
            )
            for u in users
        ],
    )


@router.post("/users/{user_id}/tickets")
async def adjust_user_tickets(
    user_id: str,
    req: AdjustTicketsRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """管理员调整用户点券余额（正数增加，负数减少）"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_balance = user.tickets + req.amount
    if new_balance < 0:
        raise HTTPException(status_code=400, detail=f"余额不足，当前 {user.tickets} 点券，不能扣 {abs(req.amount)}")

    user.tickets = new_balance
    await db.commit()

    logger.info(
        "[ADMIN] 调整点券 | user=%s amount=%+d balance_before=%d balance_after=%d by=%s",
        user.email, req.amount, user.tickets - req.amount, user.tickets, admin["email"],
    )
    return {"message": "调整成功", "tickets": user.tickets}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """管理员删除用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 管理员不能删除自己
    if user.email == admin["email"]:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    await db.delete(user)
    await db.commit()

    logger.info("[ADMIN] 删除用户 | user=%s by=%s", user.email, admin["email"])
    return {"message": f"已删除用户 {user.email}"}
