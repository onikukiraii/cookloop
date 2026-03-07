from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from entity.base import Base


class HotcookRecipeIngredient(Base):
    __tablename__ = "hotcook_recipe_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("hotcook_recipes.id"), nullable=False)
    ingredient_master_id = Column(Integer, ForeignKey("ingredient_master.id"), nullable=False)

    recipe = relationship("HotcookRecipe", back_populates="ingredients")
    ingredient_master = relationship("IngredientMaster", back_populates="recipe_ingredients")
