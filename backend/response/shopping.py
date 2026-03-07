from datetime import datetime

from pydantic import BaseModel

from entity.shopping_item import ShoppingItem


class ShoppingItemResponse(BaseModel):
    id: int
    ingredient_master_id: int
    ingredient_name: str
    source: str
    is_checked: bool
    added_at: datetime
    checked_at: datetime | None

    model_config = {"from_attributes": True}


def to_shopping_response(item: ShoppingItem) -> ShoppingItemResponse:
    return ShoppingItemResponse(
        id=item.id,  # type: ignore[arg-type]
        ingredient_master_id=item.ingredient_master_id,  # type: ignore[arg-type]
        ingredient_name=item.ingredient_master.name,
        source=item.source,  # type: ignore[arg-type]
        is_checked=item.is_checked,  # type: ignore[arg-type]
        added_at=item.added_at,  # type: ignore[arg-type]
        checked_at=item.checked_at,  # type: ignore[arg-type]
    )
