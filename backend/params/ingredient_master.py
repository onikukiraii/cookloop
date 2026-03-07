from pydantic import BaseModel


class IngredientMasterCreateParams(BaseModel):
    name: str
    default_expiry_days: int
    is_staple: bool = False


class IngredientMasterUpdateParams(BaseModel):
    default_expiry_days: int | None = None
    is_staple: bool | None = None
