import datetime

from pydantic import BaseModel

from entity.enums import QuantityStatus


class FridgeItemCreateParams(BaseModel):
    ingredient_master_id: int
    expiry_date: datetime.date | None = None
    quantity_status: QuantityStatus = QuantityStatus.full


class FridgeItemUpdateParams(BaseModel):
    quantity_status: QuantityStatus
