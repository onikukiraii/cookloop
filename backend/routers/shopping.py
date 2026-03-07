from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.fridge_item import FridgeItem
from entity.ingredient_master import IngredientMaster
from entity.shopping_item import ShoppingItem
from params.shopping import ShoppingItemCreateParams
from response.shopping import ShoppingItemResponse, to_shopping_response

router = APIRouter(prefix="/shopping", tags=["shopping"])


@router.get("/", response_model=list[ShoppingItemResponse])
def get_shopping_items(db: Session = Depends(get_db)) -> list[ShoppingItemResponse]:
    items = (
        db.query(ShoppingItem)
        .options(joinedload(ShoppingItem.ingredient_master))
        .filter(ShoppingItem.is_checked == False)  # noqa: E712
        .order_by(ShoppingItem.added_at.desc())
        .all()
    )
    return [to_shopping_response(item) for item in items]


@router.post("/", response_model=ShoppingItemResponse)
def create_shopping_item(params: ShoppingItemCreateParams, db: Session = Depends(get_db)) -> ShoppingItemResponse:
    master = db.query(IngredientMaster).filter(IngredientMaster.id == params.ingredient_master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="食材マスタが見つかりません。")

    item = ShoppingItem(
        ingredient_master_id=params.ingredient_master_id,
        source=params.source.value,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item.ingredient_master = master
    return to_shopping_response(item)


@router.patch("/{item_id}/check", response_model=ShoppingItemResponse)
def check_shopping_item(item_id: int, db: Session = Depends(get_db)) -> ShoppingItemResponse:
    item = (
        db.query(ShoppingItem)
        .options(joinedload(ShoppingItem.ingredient_master))
        .filter(ShoppingItem.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="買い物リストアイテムが見つかりません。")

    now = datetime.now(UTC)
    item.is_checked = True  # type: ignore[assignment]
    item.checked_at = now  # type: ignore[assignment]
    db.commit()
    db.refresh(item)

    master = item.ingredient_master
    expiry_date = date.today() + timedelta(days=master.default_expiry_days)
    fridge_item = FridgeItem(
        ingredient_master_id=item.ingredient_master_id,
        expiry_date=expiry_date,
        quantity_status="full",
    )
    db.add(fridge_item)
    db.commit()

    return to_shopping_response(item)


@router.delete("/{item_id}", status_code=204)
def delete_shopping_item(item_id: int, db: Session = Depends(get_db)) -> None:
    item = db.query(ShoppingItem).filter(ShoppingItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="買い物リストアイテムが見つかりません。")

    db.delete(item)
    db.commit()
