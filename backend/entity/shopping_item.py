from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class ShoppingItem(Base):
    __tablename__ = "shopping_list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient_master_id = Column(Integer, ForeignKey("ingredient_master.id"), nullable=False)
    source = Column(String(20), nullable=False, default="manual")
    is_checked = Column(Boolean, nullable=False, default=False)
    added_at = Column(DateTime, default=lambda: datetime.now(UTC))
    checked_at = Column(DateTime, nullable=True)

    ingredient_master = relationship("IngredientMaster", back_populates="shopping_items")
