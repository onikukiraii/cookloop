"""スクレイピング済みJSONをDBに投入するシードスクリプト。

Usage:
    cd backend && DATABASE_URL=mysql+pymysql://app:password@localhost:3309/cookloop \
        uv run python ../scripts/seed_db.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.hotcook_recipe_material import HotcookRecipeMaterial
from entity.hotcook_recipe_step import HotcookRecipeStep
from entity.ingredient_master import IngredientMaster
from lib.opensearch import create_ingredient_search_client

DATA_DIR = Path(__file__).resolve().parent / "output"

DEFAULT_EXPIRY_DAYS = 7


def load_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def seed(session: Session) -> None:
    # 既存データを削除（外部キー制約の順序に注意）
    print("Clearing existing data...")
    session.execute(text("DELETE FROM hotcook_recipe_ingredients"))
    session.execute(text("DELETE FROM hotcook_recipe_materials"))
    session.execute(text("DELETE FROM hotcook_recipe_steps"))
    session.execute(text("DELETE FROM hotcook_recipes"))
    session.execute(text("DELETE FROM fridge_items"))
    session.execute(text("DELETE FROM shopping_list"))
    session.execute(text("DELETE FROM ingredient_master"))
    session.commit()

    # 1. 食材マスタ投入
    print("=== Seeding ingredient_master ===")
    ingredients_data = load_json("ingredient_search.json")
    name_to_master: dict[str, IngredientMaster] = {}

    for item in ingredients_data:
        master = IngredientMaster(
            name=item["name"],
            default_expiry_days=item.get("default_expiry_days", DEFAULT_EXPIRY_DAYS),
            is_staple=False,
        )
        session.add(master)
        name_to_master[item["name"]] = master

    session.flush()  # IDを確定
    print(f"  {len(name_to_master)} ingredients inserted")

    # OpenSearchに同期
    print("\n=== Syncing to OpenSearch ===")
    try:
        search_client = create_ingredient_search_client()
        search_client.ensure_index()
        for item in ingredients_data:
            master = name_to_master[item["name"]]
            search_client.upsert(
                master.id,
                item["name"],
                aliases=item.get("aliases"),
                yomi=item.get("yomi"),
            )
        print(f"  {len(name_to_master)} ingredients synced to OpenSearch")
    except Exception as e:
        print(f"  WARNING: OpenSearch sync failed: {e}")

    # 2. レシピ投入
    print("\n=== Seeding hotcook_recipes ===")
    recipes_data = load_json("hotcook_recipes.json")

    skipped_ingredients = 0
    recipes_inserted = 0

    for recipe_data in recipes_data:
        code = recipe_data.get("code", "")
        if not code:
            continue

        # ヘルシオデリのレシピはスキップ
        if "ヘルシオデリ" in recipe_data.get("name", ""):
            continue

        recipe = HotcookRecipe(
            code=code,
            name=recipe_data["name"],
            menu_num=recipe_data.get("menu_num") or None,
            image_url=recipe_data.get("image_url") or None,
            category=recipe_data.get("category") or None,
        )
        session.add(recipe)
        session.flush()  # recipe.id を確定

        # Materials（分量付き全材料）
        for mat in recipe_data.get("materials", []):
            material = HotcookRecipeMaterial(
                recipe_id=recipe.id,
                material_order=mat.get("order_number", 0),
                name=mat["name"],
                quantity=mat.get("quantity"),
                group_name=mat.get("group"),
            )
            session.add(material)

        # Steps
        for i, step_text in enumerate(recipe_data.get("steps", []), 1):
            step = HotcookRecipeStep(
                recipe_id=recipe.id,
                step_order=i,
                text=step_text,
            )
            session.add(step)

        # Ingredients（マスタに存在するもののみ）
        for ingredient_name in recipe_data.get("ingredients", []):
            master = name_to_master.get(ingredient_name)
            if master:
                ri = HotcookRecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_master_id=master.id,
                )
                session.add(ri)
            else:
                skipped_ingredients += 1

        recipes_inserted += 1

    session.commit()
    print(f"  {recipes_inserted} recipes inserted")
    if skipped_ingredients:
        print(f"  {skipped_ingredients} ingredient links skipped (not in master)")

    print("\nDone!")


def main() -> None:
    import os

    database_url = os.environ.get("DATABASE_URL", "mysql+pymysql://app:password@localhost:3309/cookloop")
    engine = create_engine(database_url, echo=False)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        seed(session)


if __name__ == "__main__":
    main()
