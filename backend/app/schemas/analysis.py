from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AnalysisRequest(BaseModel):
    stock_code: str = Field(..., min_length=1, max_length=20, description="股票代码，如 600519")
    skill_name: str = Field(default="stock-analysis", description="Hermes skill 名称")


class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    estimated_seconds: int = 180


class AnalysisStatusResponse(BaseModel):
    task_id: str
    stock_code: str
    stock_name: Optional[str] = None
    status: str
    progress: float
    report: Optional[str] = None
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
