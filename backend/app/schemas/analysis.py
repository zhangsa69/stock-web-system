from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AnalysisRequest(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20, pattern=r"^[0-9]+$", description="股票代码，仅允许纯数字，如 600519")
    skill_name: str = Field(default="cninfo-financial-analysis", description="Hermes skill 名称")
    email: str = Field(default="", description="接收报告的邮箱（从JWT自动获取，可留空）")


class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    estimated_seconds: int = 600


class AnalysisStatusResponse(BaseModel):
    task_id: str
    stock_code: str
    stock_name: Optional[str] = None
    status: str
    progress: float
    report: Optional[str] = None
    html_report: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnalysisHistoryItem(BaseModel):
    task_id: str
    stock_code: str
    stock_name: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
