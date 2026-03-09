from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from entity.condiment_item import CondimentItem
from entity.ingredient_master import IngredientMaster
from lib.opensearch import create_ingredient_search_client
from params.condiment import CondimentCreateParams, CondimentUpdateParams
from response.condiment import CondimentResponse

router = APIRouter(prefix="/condiments", tags=["condiments"])


@router.get("/", response_model=list[CondimentResponse])
def get_condiments(db: Session = Depends(get_db)) -> list[CondimentItem]:
    from sqlalchemy import case

    quantity_order = case(
        (CondimentItem.quantity_status == "little", 0),
        (CondimentItem.quantity_status == "half", 1),
        (CondimentItem.quantity_status == "full", 2),
        else_=3,
    )
    return db.query(CondimentItem).order_by(quantity_order).all()


@router.post("/", response_model=CondimentResponse)
def create_condiment(params: CondimentCreateParams, db: Session = Depends(get_db)) -> CondimentItem:
    # IngredientMaster を検索または作成
    master = db.query(IngredientMaster).filter(IngredientMaster.name == params.name).first()
    if not master:
        master = IngredientMaster(
            name=params.name,
            default_expiry_days=365,
            is_staple=params.is_staple,
            category="condiment",
        )
        db.add(master)
        db.flush()

        try:
            search_client = create_ingredient_search_client()
            search_client.ensure_index()
            search_client.upsert(master.id, master.name)  # type: ignore[arg-type]
        except Exception:
            pass
    else:
        # 既存マスタを condiment カテゴリに更新
        master.category = "condiment"  # type: ignore[assignment]

    item = CondimentItem(
        name=params.name,
        quantity_status=params.quantity_status.value,
        is_staple=params.is_staple,
        ingredient_master_id=master.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=CondimentResponse)
def update_condiment(item_id: int, params: CondimentUpdateParams, db: Session = Depends(get_db)) -> CondimentItem:
    item = db.query(CondimentItem).filter(CondimentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="調味料が見つかりません。")

    item.quantity_status = params.quantity_status.value  # type: ignore[assignment]
    item.updated_at = datetime.now(UTC)  # type: ignore[assignment]
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_condiment(item_id: int, db: Session = Depends(get_db)) -> None:
    item = db.query(CondimentItem).filter(CondimentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="調味料が見つかりません。")

    db.delete(item)
    db.commit()
