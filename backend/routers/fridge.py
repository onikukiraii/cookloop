from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.fridge_item import FridgeItem
from entity.ingredient_master import IngredientMaster
from entity.shopping_item import ShoppingItem
from params.fridge import FridgeItemCreateParams, FridgeItemUpdateParams
from response.fridge import FridgeItemResponse, to_fridge_response

router = APIRouter(prefix="/fridge", tags=["fridge"])


@router.get("/", response_model=list[FridgeItemResponse])
def get_fridge_items(db: Session = Depends(get_db)) -> list[FridgeItemResponse]:
    items = (
        db.query(FridgeItem)
        .options(joinedload(FridgeItem.ingredient_master))
        .order_by(FridgeItem.expiry_date.asc())
        .all()
    )
    return [to_fridge_response(item) for item in items]


@router.post("/", response_model=FridgeItemResponse)
def create_fridge_item(params: FridgeItemCreateParams, db: Session = Depends(get_db)) -> FridgeItemResponse:
    master = db.query(IngredientMaster).filter(IngredientMaster.id == params.ingredient_master_id).first()
    if not master:
        raise HTTPException(status_code=404, detail="食材マスタが見つかりません。")

    expiry_date = params.expiry_date
    if expiry_date is None:
        expiry_date = date.today() + timedelta(days=master.default_expiry_days)  # type: ignore[arg-type]

    item = FridgeItem(
        ingredient_master_id=params.ingredient_master_id,
        expiry_date=expiry_date,
        quantity_status=params.quantity_status.value,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item.ingredient_master = master
    return to_fridge_response(item)


@router.patch("/{item_id}", response_model=FridgeItemResponse)
def update_fridge_item(
    item_id: int, params: FridgeItemUpdateParams, db: Session = Depends(get_db)
) -> FridgeItemResponse:
    item = (
        db.query(FridgeItem).options(joinedload(FridgeItem.ingredient_master)).filter(FridgeItem.id == item_id).first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="冷蔵庫アイテムが見つかりません。")

    item.quantity_status = params.quantity_status.value  # type: ignore[assignment]
    item.updated_at = datetime.now(UTC)  # type: ignore[assignment]
    db.commit()
    db.refresh(item)

    if params.quantity_status.value == "little" and item.ingredient_master.is_staple:
        existing = (
            db.query(ShoppingItem)
            .filter(
                ShoppingItem.ingredient_master_id == item.ingredient_master_id,
                ShoppingItem.is_checked == False,  # noqa: E712
            )
            .first()
        )
        if not existing:
            shopping_item = ShoppingItem(
                ingredient_master_id=item.ingredient_master_id,
                source="staple_auto",
            )
            db.add(shopping_item)
            db.commit()

    return to_fridge_response(item)


@router.delete("/{item_id}", status_code=204)
def delete_fridge_item(item_id: int, db: Session = Depends(get_db)) -> None:
    item = (
        db.query(FridgeItem).options(joinedload(FridgeItem.ingredient_master)).filter(FridgeItem.id == item_id).first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="冷蔵庫アイテムが見つかりません。")

    if item.ingredient_master.is_staple:
        existing = (
            db.query(ShoppingItem)
            .filter(
                ShoppingItem.ingredient_master_id == item.ingredient_master_id,
                ShoppingItem.is_checked == False,  # noqa: E712
            )
            .first()
        )
        if not existing:
            shopping_item = ShoppingItem(
                ingredient_master_id=item.ingredient_master_id,
                source="staple_auto",
            )
            db.add(shopping_item)

    db.delete(item)
    db.commit()
