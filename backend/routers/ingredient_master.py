from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.session import get_db
from entity.ingredient_master import IngredientMaster
from lib.opensearch import create_ingredient_search_client
from params.ingredient_master import IngredientMasterCreateParams, IngredientMasterUpdateParams
from response.ingredient_master import IngredientMasterResponse

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/search")
def search_ingredients(q: str = Query(..., min_length=1)) -> list[dict[str, Any]]:
    client = create_ingredient_search_client()
    return client.search(q)


@router.get("/", response_model=list[IngredientMasterResponse])
def get_ingredients(db: Session = Depends(get_db)) -> list[IngredientMaster]:
    return db.query(IngredientMaster).all()


@router.post("/", response_model=IngredientMasterResponse)
def create_ingredient(params: IngredientMasterCreateParams, db: Session = Depends(get_db)) -> IngredientMaster:
    ingredient = IngredientMaster(
        name=params.name,
        default_expiry_days=params.default_expiry_days,
        is_staple=params.is_staple,
    )
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)

    try:
        search_client = create_ingredient_search_client()
        search_client.ensure_index()
        search_client.upsert(ingredient.id, ingredient.name)  # type: ignore[arg-type]
    except Exception:
        pass  # OpenSearch unavailable should not block creation

    return ingredient


@router.patch("/{item_id}", response_model=IngredientMasterResponse)
def update_ingredient(
    item_id: int, params: IngredientMasterUpdateParams, db: Session = Depends(get_db)
) -> IngredientMaster:
    ingredient = db.query(IngredientMaster).filter(IngredientMaster.id == item_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="食材マスタが見つかりません。")

    if params.default_expiry_days is not None:
        ingredient.default_expiry_days = params.default_expiry_days  # type: ignore[assignment]
    if params.is_staple is not None:
        ingredient.is_staple = params.is_staple  # type: ignore[assignment]
    ingredient.updated_at = datetime.now(UTC)  # type: ignore[assignment]
    db.commit()
    db.refresh(ingredient)
    return ingredient
