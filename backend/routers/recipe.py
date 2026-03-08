import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.ingredient_master import IngredientMaster
from lib.opensearch import create_ingredient_search_client, create_recipe_search_client
from response.recipe import (
    RecipeDetailResponse,
    RecipeIngredientResponse,
    RecipeListResponse,
    RecipeMaterialResponse,
    RecipeStepResponse,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])
logger = logging.getLogger(__name__)

COCORO_BASE_URL = "https://cocoroplus.jp.sharp/kitchen/recipe/hotcook"


def _source_url(code: str) -> str:
    return f"{COCORO_BASE_URL}/{code}"


@router.get("/", response_model=list[RecipeListResponse])
def search_recipes(
    q: str = Query("", description="料理名または食材名で検索"),
    db: Session = Depends(get_db),
) -> list[RecipeListResponse]:
    if q.strip():
        return _search_via_opensearch(q.strip(), db)
    return _search_via_db(q, db)


def _resolve_ingredient_expansions(q: str) -> list[str]:
    """ひらがな等のクエリを食材インデックスで検索し、漢字名に展開する。"""
    try:
        ing_client = create_ingredient_search_client()
        ing_hits = ing_client.search(q, size=20)
        return [hit["name"] for hit in ing_hits if "name" in hit]
    except Exception:
        logger.debug("Ingredient expansion failed", exc_info=True)
        return []


def _search_via_opensearch(q: str, db: Session) -> list[RecipeListResponse]:
    try:
        ingredient_expansions = _resolve_ingredient_expansions(q)
        client = create_recipe_search_client()
        hits = client.search(q, ingredient_expansions=ingredient_expansions or None)
    except Exception:
        logger.warning("OpenSearch unavailable, falling back to DB search", exc_info=True)
        return _search_via_db(q, db)

    if not hits:
        return []

    hit_ids = [h["id"] for h in hits]
    recipes = (
        db.query(HotcookRecipe)
        .options(
            joinedload(HotcookRecipe.ingredients).joinedload(HotcookRecipeIngredient.ingredient_master),
        )
        .filter(HotcookRecipe.id.in_(hit_ids))
        .all()
    )

    recipe_map = {r.id: r for r in recipes}
    results: list[RecipeListResponse] = []
    for rid in hit_ids:
        r = recipe_map.get(rid)
        if r is None:
            continue
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


def _search_via_db(q: str, db: Session) -> list[RecipeListResponse]:
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
            joinedload(HotcookRecipe.materials),
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
        materials=[
            RecipeMaterialResponse(
                name=m.name,
                quantity=m.quantity,
                group_name=m.group_name,
            )
            for m in sorted(recipe.materials, key=lambda m: m.material_order)
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
