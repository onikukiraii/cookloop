from pydantic import BaseModel

from entity.enums import ShoppingSource


class ShoppingItemCreateParams(BaseModel):
    ingredient_master_id: int
    source: ShoppingSource = ShoppingSource.manual


class ShoppingItemCreateByNameParams(BaseModel):
    name: str
    source: ShoppingSource = ShoppingSource.manual
