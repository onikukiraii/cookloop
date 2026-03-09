from datetime import datetime

from pydantic import BaseModel


class IngredientMasterResponse(BaseModel):
    id: int
    name: str
    default_expiry_days: int
    is_staple: bool
    category: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
