"""充值相关 Pydantic 模型"""
from pydantic import BaseModel, Field


class RedeemRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=64, description="充值卡密")


class RedeemResponse(BaseModel):
    success: bool
    message: str
    tickets_added: int = 0
    balance: int = 0


class BalanceResponse(BaseModel):
    tickets: int
    email: str
