"""认证相关 Pydantic 模型"""
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码（6-128字符）")


class VerifyEmailRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    email: str
    is_verified: bool
    created_at: str
    tickets: int = 0

    class Config:
        from_attributes = True
