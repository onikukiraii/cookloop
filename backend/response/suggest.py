from datetime import datetime

from pydantic import BaseModel


class SuggestedStepResponse(BaseModel):
    step_order: int
    text: str


class SuggestedMaterialResponse(BaseModel):
    name: str
    quantity: str | None = None
    group_name: str | None = None


class SuggestedRecipeResponse(BaseModel):
    type: str
    name: str
    recipe_id: int | None = None
    menu_num: str | None = None
    image_url: str | None = None
    category: str = ""
    used_ingredients: list[str]
    missing_ingredients: list[str] = []
    note: str = ""
    steps: list[SuggestedStepResponse] = []
    materials: list[SuggestedMaterialResponse] = []
    manual_mode: str | None = None
    manual_stir: str | None = None
    manual_time_min: int | None = None


class SuggestResponse(BaseModel):
    suggestions: list[SuggestedRecipeResponse]


class SuggestJobCreateResponse(BaseModel):
    job_id: int


class SuggestJobStatusResponse(BaseModel):
    job_id: int
    status: str
    suggestions: list[SuggestedRecipeResponse] | None = None
    error: str | None = None
    created_at: datetime | None = None
