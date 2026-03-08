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
    menu_num: str | None = None
    image_url: str | None = None
    category: str = ""
    used_ingredients: list[str]
    missing_ingredients: list[str] = []
    note: str = ""
    steps: list[SuggestedStepResponse] = []
    materials: list[SuggestedMaterialResponse] = []


class SuggestResponse(BaseModel):
    suggestions: list[SuggestedRecipeResponse]
