"""食材マスタにGeminiで賞味期限（日数）を一括推定して付与するスクリプト。

Usage:
    cd backend && GEMINI_API_KEY=xxx uv run python ../scripts/generate_expiry_days.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from lib.gemini import create_gemini_client

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
BATCH_SIZE = 100

PROMPT_TEMPLATE = """以下の食材リストについて、冷蔵庫で保存した場合の一般的な賞味期限（日数）を推定してください。
開封後・購入後の目安日数を整数で回答してください。

ルール:
- 肉類: 2-3日
- 魚介類: 1-2日
- 葉物野菜: 3-5日
- 根菜類: 7-14日
- きのこ類: 3-5日
- 豆腐・練り物: 3-5日
- 乾物・缶詰: 30-90日
- 冷凍食品: 30日
- 卵: 14日
- 上記に当てはまらない場合は常識的に判断

食材リスト:
{ingredients}

以下のJSON配列のみを返してください:
[
  {{ "name": "食材名", "default_expiry_days": 日数 }}
]"""


def main() -> None:
    ingredients_path = OUTPUT_DIR / "ingredient_search.json"
    with open(ingredients_path, encoding="utf-8") as f:
        ingredients = json.load(f)

    # 既にdefault_expiry_daysがある食材はスキップ
    to_process = [ing for ing in ingredients if "default_expiry_days" not in ing]
    if not to_process:
        print("全食材にdefault_expiry_daysが設定済み")
        return

    print(f"{len(to_process)}/{len(ingredients)}件の食材に賞味期限を推定します")

    client = create_gemini_client()
    results: dict[str, int] = {}

    total_batches = (len(to_process) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(to_process), BATCH_SIZE):
        batch = to_process[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        names = [ing["name"] for ing in batch]

        print(f"  Batch {batch_num}/{total_batches} ({len(batch)}件)...")

        prompt = PROMPT_TEMPLATE.format(ingredients=json.dumps(names, ensure_ascii=False))

        for attempt in range(5):
            try:
                result = client.generate_json(prompt)
                break
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    wait = 2**attempt * 10
                    print(f"  [RATE LIMIT] {wait}s 待機 (attempt {attempt + 1}/5)...")
                    time.sleep(wait)
                else:
                    print(f"  [ERROR] {e}")
                    result = None
                    break
        else:
            result = None

        if result and isinstance(result, list):
            for item in result:
                name = item.get("name", "")
                days = item.get("default_expiry_days", 7)
                results[name] = days
            print(f"  Batch {batch_num} done: {len(result)}件")
        else:
            print(f"  [WARN] Batch {batch_num} スキップ")

        if i + BATCH_SIZE < len(to_process):
            time.sleep(2)

    # 結果をマージ
    updated = 0
    for ing in ingredients:
        if ing["name"] in results:
            ing["default_expiry_days"] = results[ing["name"]]
            updated += 1
        elif "default_expiry_days" not in ing:
            ing["default_expiry_days"] = 7  # フォールバック

    with open(ingredients_path, "w", encoding="utf-8") as f:
        json.dump(ingredients, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {updated}件更新、書き出し先: {ingredients_path}")


if __name__ == "__main__":
    main()
