from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class FridgeItem(Base):
    __tablename__ = "fridge_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_master_id = Column(Integer, ForeignKey("ingredient_master.id"), nullable=False)
    expiry_date = Column(Date, nullable=False)
    quantity_status = Column(String(10), nullable=False, default="full")
    registered_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    ingredient_master = relationship("IngredientMaster", back_populates="fridge_items")
