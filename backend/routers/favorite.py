from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from entity.favorite_recipe import FavoriteRecipe

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("/", response_model=list[int])
def list_favorites(db: Session = Depends(get_db)) -> list[int]:
    rows = db.query(FavoriteRecipe.recipe_id).all()
    return [r[0] for r in rows]


@router.post("/{recipe_id}")
def add_favorite(recipe_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    existing = db.query(FavoriteRecipe).filter(FavoriteRecipe.recipe_id == recipe_id).first()
    if not existing:
        db.add(FavoriteRecipe(recipe_id=recipe_id))
        db.commit()
    return {"ok": True}


@router.delete("/{recipe_id}")
def remove_favorite(recipe_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    fav = db.query(FavoriteRecipe).filter(FavoriteRecipe.recipe_id == recipe_id).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"ok": True}
