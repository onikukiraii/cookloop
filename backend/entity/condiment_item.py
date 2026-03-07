from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from entity.base import Base


class CondimentItem(Base):
    __tablename__ = "condiment_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    quantity_status = Column(String(10), nullable=False, default="full")
    is_staple = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
