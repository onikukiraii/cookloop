from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class CondimentItem(Base):
    __tablename__ = "condiment_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    quantity_status = Column(String(10), nullable=False, default="full")
    is_staple = Column(Boolean, nullable=False, default=True)
    ingredient_master_id = Column(Integer, ForeignKey("ingredient_master.id"), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    ingredient_master = relationship("IngredientMaster", back_populates="condiment_items")
