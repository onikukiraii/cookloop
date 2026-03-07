from pydantic import BaseModel

from entity.enums import QuantityStatus


class CondimentCreateParams(BaseModel):
    name: str
    quantity_status: QuantityStatus = QuantityStatus.full
    is_staple: bool = True


class CondimentUpdateParams(BaseModel):
    quantity_status: QuantityStatus
