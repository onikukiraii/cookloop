from pydantic import BaseModel


class SuggestedStepResponse(BaseModel):
    step_order: int
    text: str


class SuggestedRecipeResponse(BaseModel):
    type: str
    name: str
    menu_num: str | None = None
    image_url: str | None = None
    used_ingredients: list[str]
    missing_ingredients: list[str] = []
    note: str = ""
    steps: list[SuggestedStepResponse] = []


class SuggestResponse(BaseModel):
    suggestions: list[SuggestedRecipeResponse]
