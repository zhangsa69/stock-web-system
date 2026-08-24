"""用户驾驶舱数据模型"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class UserDashboardData(Base):
    """用户驾驶舱数据（自选股/产业链）"""
    __tablename__ = "user_dashboard_data"
    __table_args__ = (
        UniqueConstraint("user_id", "data_type", name="uq_user_dashboard_data"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_type: Mapped[str] = mapped_column(
        String(50), nullable=False  # 'watchlist' | 'chains'
    )
    data_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
