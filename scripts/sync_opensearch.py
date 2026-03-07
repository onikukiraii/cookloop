"""食材マスタをOpenSearchに全件同期するスクリプト。

JSONにaliases/yomiがある食材はそれも投入する。
JSONにない食材（手動登録分）はnameのみで投入する。

Usage:
    cd backend && DATABASE_URL=mysql+pymysql://app:password@localhost:3309/cookloop \
        uv run python ../scripts/sync_opensearch.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from entity.ingredient_master import IngredientMaster
from lib.opensearch import create_ingredient_search_client

DATA_DIR = Path(__file__).resolve().parent / "output"


def load_aliases_map() -> dict[str, dict]:
    """ingredient_search.json から name -> {aliases, yomi} のマップを作る。"""
    path = DATA_DIR / "ingredient_search.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data}


def main() -> None:
    import os

    database_url = os.environ.get("DATABASE_URL", "mysql+pymysql://app:password@localhost:3309/cookloop")
    engine = create_engine(database_url, echo=False)
    session_factory = sessionmaker(bind=engine)

    search_client = create_ingredient_search_client()
    search_client.ensure_index()

    aliases_map = load_aliases_map()

    with session_factory() as session:
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

        print("Done!")


if __name__ == "__main__":
    main()
