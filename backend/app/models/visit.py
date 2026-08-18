"""页面访问统计模型"""
from datetime import date, datetime, timezone
from sqlalchemy import Integer, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class PageVisit(Base):
    __tablename__ = "page_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_date: Mapped[date] = mapped_column(
        Date, unique=True, nullable=False, index=True
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<PageVisit {self.visit_date} count={self.count}>"