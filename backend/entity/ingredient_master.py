from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class IngredientMaster(Base):
    __tablename__ = "ingredient_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    default_expiry_days = Column(Integer, nullable=False)
    is_staple = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    fridge_items = relationship("FridgeItem", back_populates="ingredient_master")
    shopping_items = relationship("ShoppingItem", back_populates="ingredient_master")
    recipe_ingredients = relationship("HotcookRecipeIngredient", back_populates="ingredient_master")
