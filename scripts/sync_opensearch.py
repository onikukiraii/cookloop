"""食材マスタとレシピをOpenSearchに全件同期するスクリプト。

食材: JSONにaliases/yomiがある食材はそれも投入する。JSONにない食材（手動登録分）はnameのみで投入する。
レシピ: レシピ名+食材名で検索できるようrecipesインデックスに投入する。

Usage:
    cd backend && DATABASE_URL=mysql+pymysql://app:password@localhost:3309/cookloop \
        uv run python ../scripts/sync_opensearch.py

    # Docker container:
    docker compose -f compose.prod.yaml exec api uv run python /scripts/sync_opensearch.py
"""

import json
import os
import sys
from pathlib import Path

# ローカル: scripts/../backend, コンテナ: /app (WORKDIR)
_backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_backend_dir) if _backend_dir.exists() else os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload, sessionmaker

from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.ingredient_master import IngredientMaster
from lib.opensearch import create_ingredient_search_client, create_recipe_search_client

DATA_DIR = Path(__file__).resolve().parent / "output"


def load_aliases_map() -> dict[str, dict]:
    """ingredient_search.json から name -> {aliases, yomi} のマップを作る。"""
    path = DATA_DIR / "ingredient_search.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data}


def load_recipe_yomi_map() -> dict[str, dict]:
    """recipe_yomi.json から name -> {yomi, aliases} のマップを作る。"""
    path = DATA_DIR / "recipe_yomi.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data}


def main() -> None:
    import os

    recreate = "--no-recreate" not in sys.argv

    database_url = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://app:password@localhost:3309/cookloop"
    )
    engine = create_engine(database_url, echo=False)
    session_factory = sessionmaker(bind=engine)

    search_client = create_ingredient_search_client()
    search_client.ensure_index(recreate=recreate)

    aliases_map = load_aliases_map()

    with session_factory() as session:
        # 食材マスタ同期
        ingredients = session.query(IngredientMaster).all()
        print(f"Syncing {len(ingredients)} ingredients to OpenSearch...")

        for ing in ingredients:
            extra = aliases_map.get(ing.name, {})
            search_client.upsert(
                ing.id,
                ing.name,
                aliases=extra.get("aliases"),
                yomi=extra.get("yomi"),
            )

        print("Ingredients done!")

        # レシピ同期
        recipe_client = create_recipe_search_client()
        recipe_client.ensure_index(recreate=recreate)

        recipe_yomi_map = load_recipe_yomi_map()

        recipes = (
            session.query(HotcookRecipe)
            .options(
                joinedload(HotcookRecipe.ingredients).joinedload(
                    HotcookRecipeIngredient.ingredient_master
                ),
            )
            .all()
        )
        print(f"Syncing {len(recipes)} recipes to OpenSearch...")

        for recipe in recipes:
            ingredient_names = [
                ri.ingredient_master.name
                for ri in recipe.ingredients
                if ri.ingredient_master
            ]
            yomi_data = recipe_yomi_map.get(recipe.name, {})
            recipe_client.upsert(
                recipe_id=recipe.id,
                name=recipe.name,
                ingredient_names=ingredient_names,
                category=recipe.category,
                code=recipe.code,
                menu_num=recipe.menu_num,
                image_url=recipe.image_url,
                name_yomi=yomi_data.get("yomi"),
                name_aliases=yomi_data.get("aliases"),
            )

        print("Recipes done!")


if __name__ == "__main__":
    main()
