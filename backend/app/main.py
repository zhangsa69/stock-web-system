"""
FastAPI 应用入口

启动: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db, close_db
from .api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时：初始化数据库表
    await init_db()
    yield
    # 关闭时：断开数据库连接
    await close_db()


app = FastAPI(
    title="AI 股票财报分析平台",
    description="基于 Hermes Agent 的 A 股/港股财报 AI 分析服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "AI 股票财报分析平台",
        "version": "1.0.0",
        "status": "running",
    }
