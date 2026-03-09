import json
import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, sessionmaker

from db.session import SessionLocal, get_db
from entity.enums import QuantityStatus
from entity.fridge_item import FridgeItem
from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.ingredient_master import IngredientMaster
from entity.shopping_item import ShoppingItem
from entity.suggest_job import SuggestJob
from lib.gemini import GeminiClient, RateLimitError, create_gemini_client
from params.suggest import AddShoppingParams, SuggestParams
from response.suggest import (
    SuggestedMaterialResponse,
    SuggestedRecipeResponse,
    SuggestedStepResponse,
    SuggestJobCreateResponse,
    SuggestJobStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipe", tags=["suggest"])

MANUAL_COOKING_REFERENCE = """【手動調理リファレンス】
手動調理は以下のカテゴリから適切なものを選び、まぜかた・設定時間を指定してください。
※設定時間は沸とう後の加熱時間です（煮詰める・好みの加熱設定を除く）

1. 炒める（まぜる）- 火の通りやすい食材: 1-3分, 野菜+肉: 4-6分
2. 煮物を作る（まぜる/まぜない）- 火の通りやすい: 3-5分, 煮物: 10-20分, カレー等: 20-30分, じっくり: 30-60分
3. スープを作る（まぜる/まぜない）- あたため: 1-2分, みそ汁: 5-15分, スープ: 10-15分
4. 無水でゆでる（まぜない）- 葉菜: 1-2分, 果菜: 3-5分, 根菜: 15-20分
5. 蒸す（まぜない、蒸しトレイ+水200ml）- 火の通りやすい野菜: 2-3分, 根菜/肉/魚: 10-15分
6. めんをゆでる（まぜる、水1L）- パッケージ記載のゆで時間
7. 発酵・低温調理をする（まぜる/まぜない、温度35-90℃）
8. ケーキを焼く（まぜない）
9. 煮詰める（まぜない、設定時間=調理時間）
10. 好みの加熱設定（火力:強/中/弱、まぜかた:4段階）
※柔らかい食材（豆腐・魚）や煮崩れしやすい食材は「まぜない」を選択"""


def get_gemini_client() -> GeminiClient:
    return create_gemini_client()


def _build_fridge_line(item: FridgeItem) -> str:
    name = item.ingredient_master.name
    qty_label = QuantityStatus(item.quantity_status).label
    days_left = (item.expiry_date - date.today()).days
    return f"- {name}（残量：{qty_label}、残り{days_left}日）"


def _build_suggestions(
    raw: list[dict[str, Any]],
    fridge_names: set[str],
    candidate_recipes: list[HotcookRecipe],
    db: Session,
) -> list[SuggestedRecipeResponse]:
    suggestions: list[SuggestedRecipeResponse] = []
    for item in raw:
        recipe_type = item.get("type", "manual")
        recipe_name = item.get("name", "")
        menu_num = item.get("menu_num")
        used = item.get("used_ingredients", [])
        note = item.get("note", "")
        ai_steps = item.get("steps", [])
        ai_category = item.get("category", "")

        steps: list[SuggestedStepResponse] = []
        materials: list[SuggestedMaterialResponse] = []
        image_url: str | None = None
        category = str(ai_category)
        missing: list[str] = []
        recipe_id: int | None = None

        if recipe_type == "hotcook" and menu_num:
            db_recipe = (
                db.query(HotcookRecipe)
                .options(
                    joinedload(HotcookRecipe.steps),
                    joinedload(HotcookRecipe.materials),
                    joinedload(HotcookRecipe.ingredients).joinedload(HotcookRecipeIngredient.ingredient_master),
                )
                .filter(HotcookRecipe.menu_num == menu_num)
                .first()
            )
            if db_recipe:
                recipe_id = int(db_recipe.id)
                image_url = str(db_recipe.image_url) if db_recipe.image_url else None
                db_steps = sorted(db_recipe.steps, key=lambda s: s.step_order)
                steps = [SuggestedStepResponse(step_order=int(s.step_order), text=str(s.text)) for s in db_steps]
                db_materials = sorted(db_recipe.materials, key=lambda m: m.material_order)
                materials = [
                    SuggestedMaterialResponse(
                        name=str(m.name),
                        quantity=str(m.quantity) if m.quantity else None,
                        group_name=str(m.group_name) if m.group_name else None,
                    )
                    for m in db_materials
                ]
                if db_recipe.category and not category:
                    category = str(db_recipe.category)
                missing = [
                    str(ri.ingredient_master.name)
                    for ri in db_recipe.ingredients
                    if ri.ingredient_master and str(ri.ingredient_master.name) not in fridge_names
                ]

        used_list: list[str] = [str(u) for u in used] if isinstance(used, list) else []

        if not missing and used_list:
            missing = [name for name in used_list if name not in fridge_names]

        if not steps and isinstance(ai_steps, list):
            steps = [SuggestedStepResponse(step_order=i + 1, text=str(text)) for i, text in enumerate(ai_steps)]

        if not materials:
            ai_materials = item.get("materials", [])
            if isinstance(ai_materials, list):
                materials = [
                    SuggestedMaterialResponse(
                        name=m.get("name", ""),
                        quantity=m.get("quantity"),
                        group_name=None,
                    )
                    for m in ai_materials
                    if isinstance(m, dict)
                ]

        manual_mode = item.get("manual_mode") if recipe_type == "manual" else None
        manual_stir = item.get("manual_stir") if recipe_type == "manual" else None
        manual_time_min = item.get("manual_time_min") if recipe_type == "manual" else None

        suggestions.append(
            SuggestedRecipeResponse(
                type=str(recipe_type),
                name=str(recipe_name),
                recipe_id=recipe_id,
                menu_num=str(menu_num) if menu_num else None,
                image_url=image_url,
                category=category,
                used_ingredients=used_list,
                missing_ingredients=missing,
                note=str(note),
                steps=steps,
                materials=materials,
                manual_mode=str(manual_mode) if manual_mode else None,
                manual_stir=str(manual_stir) if manual_stir else None,
                manual_time_min=int(str(manual_time_min)) if manual_time_min is not None else None,
            )
        )

    return suggestions


def _run_suggest_job(
    job_id: int,
    params: SuggestParams,
    session_factory: sessionmaker[Session],
) -> None:
    db = session_factory()
    try:
        job = db.query(SuggestJob).filter(SuggestJob.id == job_id).first()
        if not job:
            return
        job.status = "running"  # type: ignore[assignment]
        db.commit()

        fridge_items = db.query(FridgeItem).options(joinedload(FridgeItem.ingredient_master)).all()

        fridge_master_ids = [item.ingredient_master_id for item in fridge_items]
        fridge_name_map: dict[int, str] = {
            item.ingredient_master_id: item.ingredient_master.name  # type: ignore[misc]
            for item in fridge_items
        }
        fridge_names = set(fridge_name_map.values())

        if params.mode == "ingredient" and params.ingredient_master_ids:
            selected_names = [fridge_name_map[mid] for mid in params.ingredient_master_ids if mid in fridge_name_map]
        else:
            selected_names = []

        candidate_recipe_ids = (
            db.query(HotcookRecipeIngredient.recipe_id)
            .filter(HotcookRecipeIngredient.ingredient_master_id.in_(fridge_master_ids))
            .group_by(HotcookRecipeIngredient.recipe_id)
            .having(func.count(HotcookRecipeIngredient.ingredient_master_id) >= 2)
            .all()
        )
        recipe_ids = [r[0] for r in candidate_recipe_ids]

        candidate_recipes: list[HotcookRecipe] = []
        if recipe_ids:
            candidate_recipes = (
                db.query(HotcookRecipe)
                .options(joinedload(HotcookRecipe.materials))
                .filter(HotcookRecipe.id.in_(recipe_ids))
                .all()
            )

        fridge_lines = "\n".join(_build_fridge_line(item) for item in fridge_items)

        recipe_lines = ""
        if candidate_recipes:
            lines = []
            for r in candidate_recipes:
                num = f"No.{r.menu_num} " if r.menu_num else ""
                cat = f" [{r.category}]" if r.category else ""
                lines.append(f"- {num}{r.name}{cat}")
            recipe_lines = "\n".join(lines)

        selected_instruction = ""
        if selected_names:
            items_text = "\n".join(f"- {n}" for n in selected_names)
            selected_instruction = f"\n\n【指定食材（優先的に使ってください）】\n{items_text}"

        prompt = f"""【冷蔵庫の状態】
{fridge_lines}
{selected_instruction}
【ホットクックで作れる候補レシピ】
{recipe_lines if recipe_lines else "（候補なし）"}

以下の条件で今夜の夕食を10品程度提案してください。
- カテゴリ別に提案する（主菜3〜4品、副菜3〜4品、汁物1〜2品、主食1品程度）
- できるだけ多くの食材を使えるレシピを優先する
- 残量「少し」の食材を優先的に消費する
- 残日数が少ない食材を優先する
- ホットクックで作れる場合はメニュー番号を添える
- ホットクックの候補にない場合は手動調理で提案してよい
- 食材が足りない場合は省略・代替を提示してよい
- 手動調理の場合は下記リファレンスを参考にmanual_mode, manual_stir, manual_time_minを必ず指定する

{MANUAL_COOKING_REFERENCE}

JSONのみで返してください。
[
  {{
    "type": "hotcook",
    "name": "料理名",
    "menu_num": "0212",
    "category": "主菜",
    "used_ingredients": ["食材1", "食材2"],
    "note": "補足"
  }},
  {{
    "type": "manual",
    "name": "料理名",
    "menu_num": null,
    "manual_mode": "煮物を作る",
    "manual_stir": "まぜない",
    "manual_time_min": 15,
    "category": "副菜",
    "used_ingredients": ["食材1"],
    "note": "補足",
    "steps": ["手順1", "手順2"],
    "materials": [{{"name": "食材1", "quantity": "100g"}}, {{"name": "食材2", "quantity": "大さじ1"}}]
  }}
]"""

        gemini = create_gemini_client()
        raw = gemini.generate_json(prompt)
        if not isinstance(raw, list):
            raw = [raw]

        suggestions = _build_suggestions(raw, fridge_names, candidate_recipes, db)

        job.result_json = json.dumps(  # type: ignore[assignment]
            [s.model_dump() for s in suggestions],
            ensure_ascii=False,
        )
        job.status = "completed"  # type: ignore[assignment]
        db.commit()

    except RateLimitError as e:
        job = db.query(SuggestJob).filter(SuggestJob.id == job_id).first()
        if job:
            job.status = "failed"  # type: ignore[assignment]
            job.error_message = str(e)  # type: ignore[assignment]
            db.commit()
    except Exception:
        logger.exception("Suggest job %d failed", job_id)
        db.rollback()
        job = db.query(SuggestJob).filter(SuggestJob.id == job_id).first()
        if job:
            job.status = "failed"  # type: ignore[assignment]
            job.error_message = "提案処理中にエラーが発生しました。"  # type: ignore[assignment]
            db.commit()
    finally:
        db.close()


def get_session_factory() -> sessionmaker[Session]:
    return SessionLocal


@router.post("/suggest", response_model=SuggestJobCreateResponse, status_code=202)
def suggest_menu(
    params: SuggestParams,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> SuggestJobCreateResponse:
    fridge_items = db.query(FridgeItem).all()
    if not fridge_items:
        raise HTTPException(status_code=400, detail="冷蔵庫に食材がありません。")

    job = SuggestJob(
        status="pending",
        params_json=json.dumps(params.model_dump(), ensure_ascii=False),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_suggest_job, int(job.id), params, session_factory)

    return SuggestJobCreateResponse(job_id=int(job.id))


@router.get("/suggest/jobs/latest", response_model=SuggestJobStatusResponse | None)
def get_latest_suggest_job(
    db: Session = Depends(get_db),
) -> SuggestJobStatusResponse | None:
    job = db.query(SuggestJob).filter(SuggestJob.status != "failed").order_by(SuggestJob.id.desc()).first()
    if not job:
        return None

    suggestions = None
    if job.status == "completed" and job.result_json:
        raw_list = json.loads(str(job.result_json))
        suggestions = [SuggestedRecipeResponse(**item) for item in raw_list]

    return SuggestJobStatusResponse(
        job_id=int(job.id),
        status=str(job.status),
        suggestions=suggestions,
        error=str(job.error_message) if job.error_message else None,
        created_at=job.created_at,  # type: ignore[arg-type]
    )


@router.get("/suggest/jobs/{job_id}", response_model=SuggestJobStatusResponse)
def get_suggest_job_status(
    job_id: int,
    db: Session = Depends(get_db),
) -> SuggestJobStatusResponse:
    job = db.query(SuggestJob).filter(SuggestJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ジョブが見つかりません。")

    suggestions = None
    if job.status == "completed" and job.result_json:
        raw_list = json.loads(str(job.result_json))
        suggestions = [SuggestedRecipeResponse(**item) for item in raw_list]

    return SuggestJobStatusResponse(
        job_id=int(job.id),
        status=str(job.status),
        suggestions=suggestions,
        error=str(job.error_message) if job.error_message else None,
        created_at=job.created_at,  # type: ignore[arg-type]
    )


@router.post("/suggest/add-shopping")
def add_shopping_from_suggest(
    params: AddShoppingParams,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    added = 0
    for name in params.ingredient_names:
        master = db.query(IngredientMaster).filter(IngredientMaster.name == name).first()
        if not master:
            continue

        existing = (
            db.query(ShoppingItem)
            .filter(
                ShoppingItem.ingredient_master_id == master.id,
                ShoppingItem.is_checked == False,  # noqa: E712
            )
            .first()
        )
        if existing:
            continue

        item = ShoppingItem(
            ingredient_master_id=master.id,
            source="recipe",
        )
        db.add(item)
        added += 1

    if added:
        db.commit()

    return {"added_count": added}
