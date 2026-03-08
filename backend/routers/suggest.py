from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from entity.enums import QuantityStatus
from entity.fridge_item import FridgeItem
from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.ingredient_master import IngredientMaster
from entity.shopping_item import ShoppingItem
from lib.gemini import GeminiClient, RateLimitError, create_gemini_client
from params.suggest import AddShoppingParams, SuggestParams
from response.suggest import SuggestedMaterialResponse, SuggestedRecipeResponse, SuggestedStepResponse, SuggestResponse

router = APIRouter(prefix="/recipe", tags=["suggest"])


def get_gemini_client() -> GeminiClient:
    return create_gemini_client()


def _build_fridge_line(item: FridgeItem) -> str:
    name = item.ingredient_master.name
    qty_label = QuantityStatus(item.quantity_status).label
    days_left = (item.expiry_date - date.today()).days
    return f"- {name}（残量：{qty_label}、残り{days_left}日）"


@router.post("/suggest", response_model=SuggestResponse)
def suggest_menu(
    params: SuggestParams,
    db: Session = Depends(get_db),
    gemini: GeminiClient = Depends(get_gemini_client),
) -> SuggestResponse:
    fridge_items = db.query(FridgeItem).options(joinedload(FridgeItem.ingredient_master)).all()
    if not fridge_items:
        raise HTTPException(status_code=400, detail="冷蔵庫に食材がありません。")

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
    recipe_category_map: dict[str, str] = {}
    if candidate_recipes:
        lines = []
        for r in candidate_recipes:
            num = f"No.{r.menu_num} " if r.menu_num else ""
            cat = f" [{r.category}]" if r.category else ""
            lines.append(f"- {num}{r.name}{cat}")
            if r.menu_num and r.category:
                recipe_category_map[str(r.menu_num)] = str(r.category)
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
    "category": "副菜",
    "used_ingredients": ["食材1"],
    "note": "補足",
    "steps": ["手順1", "手順2"],
    "materials": [{{"name": "食材1", "quantity": "100g"}}, {{"name": "食材2", "quantity": "大さじ1"}}]
  }}
]"""

    try:
        raw = gemini.generate_json(prompt)
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e
    if not isinstance(raw, list):
        raw = [raw]

    recipe_name_map: dict[str, HotcookRecipe] = {}
    if candidate_recipes:
        for r in candidate_recipes:
            recipe_name_map[r.name] = r  # type: ignore[index]

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
        category = ai_category
        missing: list[str] = []

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
                # DBの食材マスタ紐付きで不足食材を正確に算出
                missing = [
                    str(ri.ingredient_master.name)
                    for ri in db_recipe.ingredients
                    if ri.ingredient_master and str(ri.ingredient_master.name) not in fridge_names
                ]

        # hotcookでDBヒットしなかった場合やmanualの場合はGeminiのused_ingredientsから算出
        if not missing and used:
            missing = [name for name in used if name not in fridge_names]

        if not steps and ai_steps:
            steps = [SuggestedStepResponse(step_order=i + 1, text=text) for i, text in enumerate(ai_steps)]

        if not materials:
            ai_materials = item.get("materials", [])
            materials = [
                SuggestedMaterialResponse(
                    name=m.get("name", ""),
                    quantity=m.get("quantity"),
                    group_name=None,
                )
                for m in ai_materials
                if isinstance(m, dict)
            ]

        suggestions.append(
            SuggestedRecipeResponse(
                type=recipe_type,
                name=recipe_name,
                menu_num=menu_num,
                image_url=image_url,
                category=category,
                used_ingredients=used,
                missing_ingredients=missing,
                note=note,
                steps=steps,
                materials=materials,
            )
        )

    return SuggestResponse(suggestions=suggestions)


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
