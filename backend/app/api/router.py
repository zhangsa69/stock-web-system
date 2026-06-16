from fastapi import APIRouter
from .analysis import router as analysis_router
from .auth import router as auth_router

router = APIRouter()
router.include_router(analysis_router, prefix="/api", tags=["analysis"])
router.include_router(auth_router, prefix="/api", tags=["auth"])
