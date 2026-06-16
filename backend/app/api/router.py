from fastapi import APIRouter
from .analysis import router as analysis_router
from .auth import router as auth_router
from .recharge import router as recharge_router
from .admin import router as admin_router

router = APIRouter()
router.include_router(analysis_router, prefix="/api", tags=["analysis"])
router.include_router(auth_router, prefix="/api", tags=["auth"])
router.include_router(recharge_router, prefix="/api", tags=["recharge"])
router.include_router(admin_router, prefix="/api", tags=["admin"])
