"""认证服务：注册、验证码、登录、JWT"""
import secrets
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.user import User

logger = logging.getLogger("stock-analysis.auth")


# ============ 密码哈希 ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ============ 验证码 ============

def generate_verification_code() -> str:
    """生成6位数字验证码"""
    return str(secrets.randbelow(1_000_000)).zfill(6)


# ============ JWT ============

def create_access_token(user_id: str, email: str) -> str:
    """签发 JWT access token"""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """解码 JWT token，无效/过期返回 None"""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None


# ============ 业务逻辑 ============

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str) -> tuple[bool, str]:
        """注册新用户。返回 (成功, 消息)"""
        email = email.strip().lower()

        # 检查是否已存在
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return False, "该邮箱已注册"

        code = generate_verification_code()
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_verified=False,
            verification_code=code,
            verification_code_expires_at=expires,
        )
        self.db.add(user)
        await self.db.flush()

        # 发送验证码邮件
        try:
            from ..services.email_service import EmailService
            await EmailService.send_verification_code(email, code)
        except Exception as e:
            logger.error("发送验证码失败: %s", str(e), exc_info=True)
            return False, "验证码发送失败，请稍后重试"

        logger.info("用户注册成功: %s", email)
        return True, f"验证码已发送至 {email}，10分钟内有效"

    async def verify_email(self, email: str, code: str) -> tuple[bool, str]:
        """验证邮箱"""
        email = email.strip().lower()
        code = code.strip()

        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False, "用户不存在"

        if user.is_verified:
            return True, "邮箱已验证，无需重复验证"

        if not user.verification_code or not user.verification_code_expires_at:
            return False, "未发送验证码，请先注册"

        if datetime.now(timezone.utc) > user.verification_code_expires_at:
            return False, "验证码已过期，请重新注册"

        if user.verification_code != code:
            return False, "验证码错误"

        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        await self.db.flush()

        logger.info("邮箱验证成功: %s", email)
        return True, "邮箱验证成功"

    async def login(self, email: str, password: str) -> tuple[str | None, str]:
        """登录。返回 (token, 消息)"""
        email = email.strip().lower()

        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None, "邮箱或密码错误"

        if not user.is_verified:
            return None, "邮箱尚未验证，请先完成验证"

        if not verify_password(password, user.hashed_password):
            return None, "邮箱或密码错误"

        token = create_access_token(user.id, user.email)
        logger.info("用户登录成功: %s", email)
        return token, "登录成功"

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
