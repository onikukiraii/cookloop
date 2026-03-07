from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.ingredient_master import IngredientMaster
from response.recipe import RecipeDetailResponse, RecipeIngredientResponse, RecipeListResponse, RecipeStepResponse

router = APIRouter(prefix="/recipes", tags=["recipes"])

COCORO_BASE_URL = "https://cocoroplus.jp.sharp/kitchen/recipe/hotcook"


def _source_url(code: str) -> str:
    return f"{COCORO_BASE_URL}/{code}"


@router.get("/", response_model=list[RecipeListResponse])
def search_recipes(
    q: str = Query("", description="料理名または食材名で検索"),
    db: Session = Depends(get_db),
) -> list[RecipeListResponse]:
    query = db.query(HotcookRecipe).options(
        joinedload(HotcookRecipe.ingredients).joinedload(HotcookRecipeIngredient.ingredient_master),
    )

    keywords = q.split()
    if keywords:
        conditions = []
        for kw in keywords:
            pattern = f"%{kw}%"
            master_ids = [
                mid for (mid,) in db.query(IngredientMaster.id).filter(IngredientMaster.name.like(pattern)).all()
            ]
            conditions.append(
                or_(
                    HotcookRecipe.name.like(pattern),
                    HotcookRecipe.ingredients.any(HotcookRecipeIngredient.ingredient_master_id.in_(master_ids)),
                )
            )
        query = query.filter(and_(*conditions))

    recipes = query.order_by(HotcookRecipe.name).limit(50).all()

    results: list[RecipeListResponse] = []
    for r in recipes:
        ingredient_names = [ri.ingredient_master.name for ri in r.ingredients if ri.ingredient_master]
        results.append(
            RecipeListResponse(
                id=r.id,  # type: ignore[arg-type]
                code=r.code,  # type: ignore[arg-type]
                name=r.name,  # type: ignore[arg-type]
                menu_num=r.menu_num,  # type: ignore[arg-type]
                image_url=r.image_url,  # type: ignore[arg-type]
                ingredient_names=ingredient_names,
            )
        )
    return results


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)) -> RecipeDetailResponse:
    recipe = (
        db.query(HotcookRecipe)
        .options(
            joinedload(HotcookRecipe.ingredients).joinedload(HotcookRecipeIngredient.ingredient_master),
            joinedload(HotcookRecipe.steps),
        )
        .filter(HotcookRecipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="レシピが見つかりません。")

    return RecipeDetailResponse(
        id=recipe.id,  # type: ignore[arg-type]
        code=recipe.code,  # type: ignore[arg-type]
        name=recipe.name,  # type: ignore[arg-type]
        menu_num=recipe.menu_num,  # type: ignore[arg-type]
        image_url=recipe.image_url,  # type: ignore[arg-type]
        source_url=_source_url(recipe.code),  # type: ignore[arg-type]
        ingredients=[
            RecipeIngredientResponse(
                id=ri.ingredient_master.id,
                name=ri.ingredient_master.name,
            )
            for ri in recipe.ingredients
            if ri.ingredient_master
        ],
        steps=sorted(
            [
                RecipeStepResponse(
                    step_order=s.step_order,
                    text=s.text,
                )
                for s in recipe.steps
            ],
            key=lambda s: s.step_order,
        ),
    )
