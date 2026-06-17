"""认证服务：注册、验证码、登录、JWT"""
import json
import secrets
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import redis.asyncio as aioredis
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


# ============ Redis 待验证注册 ============

PENDING_REGISTER_PREFIX = "pending_register:"
PENDING_TTL = 600  # 10 分钟


async def _get_redis():
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def _save_pending(email: str, password_hash: str, code: str):
    """存待验证注册到 Redis，10 分钟过期"""
    redis = await _get_redis()
    key = f"{PENDING_REGISTER_PREFIX}{email}"
    payload = json.dumps({
        "password_hash": password_hash,
        "code": code,
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    })
    await redis.setex(key, PENDING_TTL, payload)
    await redis.close()


async def _load_pending(email: str) -> dict | None:
    """从 Redis 取待验证注册"""
    redis = await _get_redis()
    key = f"{PENDING_REGISTER_PREFIX}{email}"
    raw = await redis.get(key)
    await redis.close()
    if not raw:
        return None
    return json.loads(raw)


async def _delete_pending(email: str):
    """删除待验证注册"""
    redis = await _get_redis()
    key = f"{PENDING_REGISTER_PREFIX}{email}"
    await redis.delete(key)
    await redis.close()


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
        """注册新用户 — 仅存 Redis，验证通过后才入库。返回 (成功, 消息)"""
        email = email.strip().lower()

        # 1. 检查是否已验证用户（已在 PG 中）
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return False, "该邮箱已注册"

        # 2. 检查是否已有待验证注册（Redis 中）
        pending = await _load_pending(email)
        if pending:
            return False, "验证码已发送，请检查邮箱（10分钟内有效）"

        # 3. 生成验证码，存 Redis
        code = generate_verification_code()
        hashed = hash_password(password)
        await _save_pending(email, hashed, code)

        # 4. 发送验证码邮件
        try:
            from ..services.email_service import EmailService
            await EmailService.send_verification_code(email, code)
        except Exception as e:
            logger.error("发送验证码失败: %s", str(e), exc_info=True)
            await _delete_pending(email)  # 发邮件失败，清理 Redis
            return False, "验证码发送失败，请稍后重试"

        logger.info("用户注册（待验证）: %s", email)
        return True, f"验证码已发送至 {email}，10分钟内有效"

    async def verify_email(self, email: str, code: str) -> tuple[bool, str]:
        """验证邮箱 — 从 Redis 取待验证数据，验证通过才入库"""
        email = email.strip().lower()
        code = code.strip()

        # 1. 从 Redis 取待验证注册
        pending = await _load_pending(email)
        if not pending:
            return False, "验证码已过期或未注册，请重新注册"

        # 2. 验证验证码
        if pending["code"] != code:
            return False, "验证码错误"

        # 3. 验证通过 → 创建用户到 PG
        user = User(
            email=email,
            hashed_password=pending["password_hash"],
            is_verified=True,
        )
        self.db.add(user)
        await self.db.flush()

        # 4. 清理 Redis
        await _delete_pending(email)

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
