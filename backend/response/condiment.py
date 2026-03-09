from datetime import datetime

from pydantic import BaseModel


class CondimentResponse(BaseModel):
    id: int
    name: str
    quantity_status: str
    is_staple: bool
    ingredient_master_id: int | None
    updated_at: datetime

    model_config = {"from_attributes": True}
