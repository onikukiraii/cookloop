from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from entity.condiment_item import CondimentItem
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
    item = CondimentItem(
        name=params.name,
        quantity_status=params.quantity_status.value,
        is_staple=params.is_staple,
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
