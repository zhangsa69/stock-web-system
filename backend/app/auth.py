"""认证 API 路由：注册、验证、登录、个人信息"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册 — 发送邮箱验证码"""
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
        created_at=u.created_at.isoformat(),
    )
