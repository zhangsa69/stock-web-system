"""充值卡密模型"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class RechargeCode(Base):
    __tablename__ = "recharge_codes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    ticket_value: Mapped[int] = mapped_column(Integer, nullable=False)  # 2 / 30 / 50 / 100
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    used_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # user email
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<RechargeCode {self.code[:8]}... value={self.ticket_value} used={self.is_used}>"
