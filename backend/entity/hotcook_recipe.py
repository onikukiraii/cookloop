from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class HotcookRecipe(Base):
    __tablename__ = "hotcook_recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    menu_num = Column(String(10), nullable=True)
    image_url = Column(String(500), nullable=True)
    category = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    ingredients = relationship("HotcookRecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    steps = relationship("HotcookRecipeStep", back_populates="recipe", cascade="all, delete-orphan")
    materials = relationship("HotcookRecipeMaterial", back_populates="recipe", cascade="all, delete-orphan")
    favorite = relationship("FavoriteRecipe", back_populates="recipe", uselist=False, cascade="all, delete-orphan")
