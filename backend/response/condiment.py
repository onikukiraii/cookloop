from datetime import datetime

from pydantic import BaseModel


class CondimentResponse(BaseModel):
    id: int
    name: str
    quantity_status: str
    is_staple: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
