from pydantic import BaseModel


class SuggestParams(BaseModel):
    mode: str = "omakase"
    ingredient_master_ids: list[int] = []


class AddShoppingParams(BaseModel):
    ingredient_names: list[str]
