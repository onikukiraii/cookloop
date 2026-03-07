from datetime import datetime

from pydantic import BaseModel


class IngredientMasterResponse(BaseModel):
    id: int
    name: str
    default_expiry_days: int
    is_staple: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
