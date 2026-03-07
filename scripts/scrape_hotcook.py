"""COCORO KITCHENからホットクック(KN-HW24H)の全レシピをスクレイピングし、
アプリDB用JSON + OpenSearch食材マスタ用JSONを生成する。

Usage:
    cd backend && GEMINI_API_KEY=xxx uv run python ../scripts/scrape_hotcook.py

失敗したコードだけリトライ:
    cd backend && GEMINI_API_KEY=xxx uv run python ../scripts/scrape_hotcook.py --retry
"""

import argparse
import asyncio
import functools
import json
import sys
import time
from pathlib import Path

import httpx

# バックグラウンド実行時にログがバッファリングされないようにする
print = functools.partial(print, flush=True)  # type: ignore[assignment]

# backend/ を sys.path に追加して lib.gemini をインポートできるようにする
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from lib.gemini import create_gemini_client  # noqa: E402

BASE_URL = "https://cocoroplus.jp.sharp/kitchen/recipe/api/recipe"
MODEL_CODE = "KN-HW24H"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

GEMINI_BATCH_SIZE = 50

# 同時リクエスト数の上限（サーバーに負荷をかけすぎない）
MAX_CONCURRENCY = 10
# HTTPタイムアウト（秒）- ハングを防ぐ
REQUEST_TIMEOUT = 15


# ---------------------------------------------------------------------------
# 1. 一覧取得
# ---------------------------------------------------------------------------
async def fetch_recipe_list(client: httpx.AsyncClient) -> list[dict]:
    """POST APIで全レシピコードを取得する。"""
    url = f"{BASE_URL}/search"
    payload = {
        "offset": 0,
        "limit": 700,
        "search": "",
        "models": [MODEL_CODE],
        "cooktime": "",
        "reservation": False,
        "ignore_text": "",
        "purposes": [],
        "categories": [],
        "genres": [],
    }
    resp = await client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data


# ---------------------------------------------------------------------------
# 2. 詳細取得（並列）
# ---------------------------------------------------------------------------
async def fetch_recipe_detail(
    client: httpx.AsyncClient,
    code: str,
    semaphore: asyncio.Semaphore,
    counter: dict,
    total: int,
) -> tuple[str, dict | None]:
    """個別レシピの詳細を取得する。(code, result|None)を返す。"""
    url = f"{BASE_URL}/{code}/{MODEL_CODE}"
    async with semaphore:
        try:
            resp = await client.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            counter["done"] += 1
            print(f"  [{counter['done']}/{total}] {code} OK")
            return (code, resp.json())
        except httpx.HTTPError as e:
            counter["done"] += 1
            counter["fail"] += 1
            print(f"  [{counter['done']}/{total}] {code} FAILED: {e}")
            return (code, None)


async def fetch_all_details(
    client: httpx.AsyncClient, codes: list[str]
) -> tuple[list[dict], list[str]]:
    """全レシピ詳細を並列取得する。"""
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    counter = {"done": 0, "fail": 0}
    tasks = [
        fetch_recipe_detail(client, code, semaphore, counter, len(codes))
        for code in codes
    ]
    results = await asyncio.gather(*tasks)

    details: list[dict] = []
    failed_codes: list[str] = []
    for code, result in results:
        if result is not None:
            details.append(result)
        else:
            failed_codes.append(code)

    return details, failed_codes


# ---------------------------------------------------------------------------
# 3. 食材抽出（括弧除去のみ、調味料フィルタはGeminiに委譲）
# ---------------------------------------------------------------------------
def extract_raw_ingredients(recipes: list[dict]) -> list[str]:
    """全レシピから materials[].name を収集しユニークリスト化する。"""
    names: set[str] = set()
    for recipe in recipes:
        for mat in recipe.get("materials", []):
            names.add(mat["name"])
    return sorted(names)


# ---------------------------------------------------------------------------
# 4. Geminiバッチ処理
# ---------------------------------------------------------------------------
GEMINI_PROMPT_TEMPLATE = """以下の食材リストについて処理してください。

① 括弧内（全角・半角とも）を除去して食材名だけにする
② 調味料・油脂類・風味付け素材・アルコール類を除外する
  （塩、こしょう、砂糖、醤油、みりん、酒、味噌、酢、ケチャップ、油、バター、
   オリーブオイル、白ワイン、料理酒、レモン汁、だし、コンソメ、マヨネーズ、
   ソース、ドレッシング、片栗粉、小麦粉、パン粉 等）
③ 残った食材それぞれについて、表記揺れ・別名(aliases)と読み仮名(yomi)を生成する

食材リスト：
{ingredients}

以下のJSON配列のみを返してください。除外した食材は含めないでください。
[
  {{ "original": "元の名前", "name": "正規化後の名前", "yomi": "読み仮名", "aliases": ["別名1", "別名2"] }}
]"""


def normalize_ingredients_with_gemini(
    raw_ingredients: list[str],
) -> tuple[dict[str, dict], list[str]]:
    """Geminiで食材を正規化し、(正規化マップ, 除外リスト)を返す。

    Returns:
        normalized_map: {元の名前: {"name": ..., "yomi": ..., "aliases": [...]}}
        excluded: 除外された食材名のリスト
    """
    client = create_gemini_client()
    normalized_map: dict[str, dict] = {}
    all_originals_returned: set[str] = set()

    total_batches = (len(raw_ingredients) + GEMINI_BATCH_SIZE - 1) // GEMINI_BATCH_SIZE
    for i in range(0, len(raw_ingredients), GEMINI_BATCH_SIZE):
        batch = raw_ingredients[i : i + GEMINI_BATCH_SIZE]
        batch_num = i // GEMINI_BATCH_SIZE + 1
        print(f"  Gemini batch {batch_num}/{total_batches} ({len(batch)} items)...")

        prompt = GEMINI_PROMPT_TEMPLATE.format(ingredients=json.dumps(batch, ensure_ascii=False))

        # レートリミット対策: リトライ付きで呼び出す
        result = None
        for attempt in range(5):
            try:
                result = client.generate_json(prompt)
                break
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    wait = 2 ** attempt * 10  # 10, 20, 40, 80, 160秒
                    print(f"  [RATE LIMIT] Waiting {wait}s before retry (attempt {attempt + 1}/5)...")
                    time.sleep(wait)
                else:
                    print(f"  [ERROR] Gemini call failed: {e}")
                    break

        if result is None or not isinstance(result, list):
            print(f"  [WARN] Skipping batch {batch_num} (no valid result)")
            continue

        for item in result:
            original = item.get("original", "")
            all_originals_returned.add(original)
            normalized_map[original] = {
                "name": item["name"],
                "yomi": item["yomi"],
                "aliases": item.get("aliases", []),
            }

        print(f"  Gemini batch {batch_num}/{total_batches} done")

        # Gemini APIのレートリミット対策
        if i + GEMINI_BATCH_SIZE < len(raw_ingredients):
            time.sleep(2)

    excluded = [ing for ing in raw_ingredients if ing not in all_originals_returned]
    return normalized_map, excluded


# ---------------------------------------------------------------------------
# 5. レシピデータ整形
# ---------------------------------------------------------------------------
def build_recipe_output(detail: dict, normalized_map: dict[str, dict]) -> dict:
    """詳細APIレスポンスを出力形式に変換する。"""
    ingredients: list[str] = []
    for mat in detail.get("materials", []):
        raw_name = mat["name"]
        if raw_name in normalized_map:
            norm_name = normalized_map[raw_name]["name"]
            if norm_name not in ingredients:
                ingredients.append(norm_name)

    # stepsの構築: procedures があればそれを使う
    steps: list[str] = []
    for proc in detail.get("procedures", []):
        text = proc.get("text", "").strip()
        if text:
            steps.append(text)

    return {
        "code": detail.get("code", ""),
        "name": detail.get("name", ""),
        "menu_num": detail.get("menuNum"),
        "ingredients": ingredients,
        "image_url": detail.get("imageUrl", ""),
        "steps": steps,
    }


# ---------------------------------------------------------------------------
# 6. 食材マスタ構築
# ---------------------------------------------------------------------------
def build_ingredient_master(normalized_map: dict[str, dict]) -> list[dict]:
    """ユニークな正規化済み食材のマスタリストを構築する。"""
    seen: dict[str, dict] = {}
    for info in normalized_map.values():
        name = info["name"]
        if name not in seen:
            seen[name] = {
                "name": name,
                "yomi": info["yomi"],
                "aliases": info["aliases"],
            }
        else:
            # 別名をマージ
            existing_aliases = set(seen[name]["aliases"])
            existing_aliases.update(info["aliases"])
            seen[name]["aliases"] = sorted(existing_aliases)

    return sorted(seen.values(), key=lambda x: x["yomi"])


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def save_failed_codes(failed_codes: list[str]) -> None:
    """失敗コードをファイルに保存する。"""
    failed_path = OUTPUT_DIR / "failed_codes.json"
    with open(failed_path, "w", encoding="utf-8") as f:
        json.dump(failed_codes, f, ensure_ascii=False, indent=2)
    print(f"  Written: {failed_path} ({len(failed_codes)} codes)")


def load_failed_codes() -> list[str]:
    """保存済みの失敗コードを読み込む。"""
    failed_path = OUTPUT_DIR / "failed_codes.json"
    if not failed_path.exists():
        print(f"  [ERROR] {failed_path} が見つからない")
        sys.exit(1)
    with open(failed_path, encoding="utf-8") as f:
        codes = json.load(f)
    print(f"  {len(codes)} failed codes loaded from {failed_path}")
    return codes


async def async_main(retry_mode: bool = False, scrape_only: bool = False) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        if retry_mode:
            # リトライモード: 失敗コードだけ再取得
            print("=== Retry mode: fetching previously failed codes ===")
            codes = load_failed_codes()

            print(f"\n=== Fetching {len(codes)} failed recipes (concurrency={MAX_CONCURRENCY}) ===")
            details, still_failed = await fetch_all_details(client, codes)

            # 既存のレシピJSONにマージ
            recipes_path = OUTPUT_DIR / "hotcook_recipes.json"
            if recipes_path.exists():
                with open(recipes_path, encoding="utf-8") as f:
                    existing_recipes = json.load(f)
                existing_codes = {r["code"] for r in existing_recipes}
                print(f"  Existing recipes: {len(existing_recipes)}")
            else:
                existing_recipes = []
                existing_codes = set()

            # 既存の食材マスタを読む
            ingredients_path = OUTPUT_DIR / "ingredient_search.json"
            if ingredients_path.exists():
                with open(ingredients_path, encoding="utf-8") as f:
                    existing_master = json.load(f)
            else:
                existing_master = []

            # 新しく取れた詳細からレシピ出力を構築（Gemini再実行は省略、食材なしで追加）
            # TODO: 必要なら Gemini 正規化もリトライ時に再実行する
            for d in details:
                code = d.get("code", "")
                if code not in existing_codes:
                    recipe_out = {
                        "code": code,
                        "name": d.get("name", ""),
                        "menu_num": d.get("menuNum"),
                        "ingredients": [],
                        "image_url": d.get("imageUrl", ""),
                        "steps": [p.get("text", "").strip() for p in d.get("procedures", []) if p.get("text", "").strip()],
                    }
                    existing_recipes.append(recipe_out)

            with open(recipes_path, "w", encoding="utf-8") as f:
                json.dump(existing_recipes, f, ensure_ascii=False, indent=2)
            print(f"  Updated: {recipes_path} ({len(existing_recipes)} recipes)")

            if still_failed:
                save_failed_codes(still_failed)
                print(f"\n  Still failed: {len(still_failed)} codes (saved for next retry)")
            else:
                # 全部成功したら failed_codes.json を削除
                failed_path = OUTPUT_DIR / "failed_codes.json"
                if failed_path.exists():
                    failed_path.unlink()
                    print("  All retries succeeded! Removed failed_codes.json")

        else:
            # 通常モード
            # Step 1: 一覧取得
            print("=== Step 1: Fetching recipe list ===")
            data = await fetch_recipe_list(client)
            recipe_list = data["recipes"]
            codes = [r["code"] for r in recipe_list]
            print(f"  Step 1 done: {len(codes)} recipe codes retrieved")

            # Step 2: 詳細取得（並列）
            print(f"\n=== Step 2: Fetching recipe details (concurrency={MAX_CONCURRENCY}) ===")
            details, failed_codes = await fetch_all_details(client, codes)
            print(f"\n  Step 2 done: success={len(details)}, failed={len(failed_codes)}")
            if failed_codes:
                save_failed_codes(failed_codes)

    # 詳細データを中間ファイルに保存（Gemini失敗時に再利用可能）
    details_path = OUTPUT_DIR / "recipe_details_raw.json"
    with open(details_path, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print(f"  Saved raw details: {details_path}")

    if scrape_only:
        print("\n--scrape-only: スクレイピングのみ完了。")
        return

    # Step 3: 食材抽出
    print("\n=== Step 3: Extracting ingredients ===")
    raw_ingredients = extract_raw_ingredients(details)
    print(f"  Step 3 done: {len(raw_ingredients)} unique raw ingredient names")

    # Step 4: Gemini正規化
    print("\n=== Step 4: Normalizing ingredients with Gemini ===")
    normalized_map, excluded = normalize_ingredients_with_gemini(raw_ingredients)
    print(f"  Step 4 done: normalized={len(normalized_map)}, excluded={len(excluded)}")
    if excluded:
        print(f"  Excluded samples: {excluded[:10]}...")

    # Step 5: 出力JSON生成
    print("\n=== Step 5: Building output JSONs ===")
    recipes_output = [build_recipe_output(d, normalized_map) for d in details]

    ingredient_master = build_ingredient_master(normalized_map)

    # 書き出し
    recipes_path = OUTPUT_DIR / "hotcook_recipes.json"
    ingredients_path = OUTPUT_DIR / "ingredient_search.json"

    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(recipes_output, f, ensure_ascii=False, indent=2)
    print(f"  Written: {recipes_path} ({len(recipes_output)} recipes)")

    with open(ingredients_path, "w", encoding="utf-8") as f:
        json.dump(ingredient_master, f, ensure_ascii=False, indent=2)
    print(f"  Written: {ingredients_path} ({len(ingredient_master)} ingredients)")

    elapsed = time.perf_counter() - t_start
    print(f"\nDone! ({elapsed:.1f}s)")


def run_gemini_only() -> None:
    """保存済みの詳細データからGemini正規化 + JSON出力だけ実行する。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    details_path = OUTPUT_DIR / "recipe_details_raw.json"
    if not details_path.exists():
        print(f"[ERROR] {details_path} が見つからない。先に通常モードで実行してね。")
        sys.exit(1)

    with open(details_path, encoding="utf-8") as f:
        details = json.load(f)
    print(f"Loaded {len(details)} recipe details from {details_path}")

    # Step 3: 食材抽出
    print("\n=== Step 3: Extracting ingredients ===")
    raw_ingredients = extract_raw_ingredients(details)
    print(f"  Step 3 done: {len(raw_ingredients)} unique raw ingredient names")

    # Step 4: Gemini正規化
    print("\n=== Step 4: Normalizing ingredients with Gemini ===")
    normalized_map, excluded = normalize_ingredients_with_gemini(raw_ingredients)
    print(f"  Step 4 done: normalized={len(normalized_map)}, excluded={len(excluded)}")
    if excluded:
        print(f"  Excluded samples: {excluded[:10]}...")

    # Step 5: 出力JSON生成
    print("\n=== Step 5: Building output JSONs ===")
    recipes_output = [build_recipe_output(d, normalized_map) for d in details]
    ingredient_master = build_ingredient_master(normalized_map)

    recipes_path = OUTPUT_DIR / "hotcook_recipes.json"
    ingredients_path = OUTPUT_DIR / "ingredient_search.json"

    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(recipes_output, f, ensure_ascii=False, indent=2)
    print(f"  Written: {recipes_path} ({len(recipes_output)} recipes)")

    with open(ingredients_path, "w", encoding="utf-8") as f:
        json.dump(ingredient_master, f, ensure_ascii=False, indent=2)
    print(f"  Written: {ingredients_path} ({len(ingredient_master)} ingredients)")

    print("\nDone!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hotcook recipe scraper")
    parser.add_argument("--retry", action="store_true", help="Retry failed codes only")
    parser.add_argument("--gemini-only", action="store_true", help="Skip scraping, run Gemini normalization on saved details")
    parser.add_argument("--scrape-only", action="store_true", help="Scrape only (Step 1-2), save raw details and exit")
    args = parser.parse_args()

    if args.gemini_only:
        run_gemini_only()
    else:
        asyncio.run(async_main(retry_mode=args.retry, scrape_only=args.scrape_only))


if __name__ == "__main__":
    main()
