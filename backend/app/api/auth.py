"""认证 API 路由：注册、验证、登录、个人信息"""
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..schemas.auth import (
    RegisterRequest,
    VerifyEmailRequest,
    LoginRequest,
    TokenResponse,
    UserInfo,
)
from ..services.auth_service import AuthService
from ..utils.auth import get_current_user

logger = logging.getLogger("stock-analysis.api.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


async def _check_register_rate(email: str):
    """注册验证码频率限制：同一邮箱 60 秒内只能发 1 次，同一 IP 每分钟 3 次"""
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        email_key = f"rate:register:email:{email}"
        if await redis.exists(email_key):
            await redis.close()
            raise HTTPException(status_code=429, detail="验证码发送过于频繁，请60秒后再试")
        await redis.setex(email_key, 60, "1")
    finally:
        await redis.close()


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册 — 发送邮箱验证码"""
    await _check_register_rate(req.email)
    service = AuthService(db)
    ok, msg = await service.register(req.email, req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """验证邮箱验证码"""
    service = AuthService(db)
    ok, msg = await service.verify_email(req.email, req.code)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录 — 返回 JWT token"""
    service = AuthService(db)
    token, msg = await service.login(req.email, req.password)
    if not token:
        raise HTTPException(status_code=401, detail=msg)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserInfo)
async def get_me(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户信息"""
    service = AuthService(db)
    u = await service.get_user_by_email(user["email"])
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInfo(
        id=u.id,
        email=u.email,
        is_verified=u.is_verified,
        tickets=u.tickets,
        created_at=u.created_at.isoformat(),
    )
