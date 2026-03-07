import datetime

from pydantic import BaseModel

from entity.fridge_item import FridgeItem


class FridgeItemResponse(BaseModel):
    id: int
    ingredient_master_id: int
    ingredient_name: str
    expiry_date: datetime.date
    quantity_status: str
    registered_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


def to_fridge_response(item: FridgeItem) -> FridgeItemResponse:
    return FridgeItemResponse(
        id=item.id,  # type: ignore[arg-type]
        ingredient_master_id=item.ingredient_master_id,  # type: ignore[arg-type]
        ingredient_name=item.ingredient_master.name,
        expiry_date=item.expiry_date,  # type: ignore[arg-type]
        quantity_status=item.quantity_status,  # type: ignore[arg-type]
        registered_at=item.registered_at,  # type: ignore[arg-type]
        updated_at=item.updated_at,  # type: ignore[arg-type]
    )
