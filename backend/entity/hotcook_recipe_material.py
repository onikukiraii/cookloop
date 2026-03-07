from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class HotcookRecipeMaterial(Base):
    __tablename__ = "hotcook_recipe_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("hotcook_recipes.id"), nullable=False)
    material_order = Column(Integer, nullable=False)
    name = Column(String(200), nullable=False)
    quantity = Column(String(100), nullable=True)
    group_name = Column(String(50), nullable=True)

    recipe = relationship("HotcookRecipe", back_populates="materials")
