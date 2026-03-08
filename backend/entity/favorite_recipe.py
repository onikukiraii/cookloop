from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from entity.base import Base


class FavoriteRecipe(Base):
    __tablename__ = "favorite_recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("hotcook_recipes.id"), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    recipe = relationship("HotcookRecipe", back_populates="favorite")
