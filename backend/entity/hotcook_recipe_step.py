from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from entity.base import Base


class HotcookRecipeStep(Base):
    __tablename__ = "hotcook_recipe_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("hotcook_recipes.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    recipe = relationship("HotcookRecipe", back_populates="steps")
