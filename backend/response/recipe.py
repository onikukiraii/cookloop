from pydantic import BaseModel


class RecipeIngredientResponse(BaseModel):
    id: int
    name: str


class RecipeStepResponse(BaseModel):
    step_order: int
    text: str


class RecipeListResponse(BaseModel):
    id: int
    code: str
    name: str
    menu_num: str | None
    image_url: str | None
    ingredient_names: list[str]


class RecipeDetailResponse(BaseModel):
    id: int
    code: str
    name: str
    menu_num: str | None
    image_url: str | None
    source_url: str
    ingredients: list[RecipeIngredientResponse]
    steps: list[RecipeStepResponse]
