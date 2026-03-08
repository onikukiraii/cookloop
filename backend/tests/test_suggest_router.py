from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

from entity.shopping_item import ShoppingItem

MOCK_GEMINI_RESPONSE = [
    {
        "type": "hotcook",
        "name": "豚汁",
        "menu_num": "0001",
        "category": "汁物",
        "used_ingredients": ["豚バラ肉", "玉ねぎ"],
        "note": "定番の豚汁",
    },
    {
        "type": "manual",
        "name": "野菜炒め",
        "menu_num": None,
        "category": "主菜",
        "used_ingredients": ["豚バラ肉", "玉ねぎ", "にんじん"],
        "note": "",
        "steps": ["材料を切る", "炒める", "味付けする"],
        "materials": [
            {"name": "豚バラ肉", "quantity": "200g"},
            {"name": "玉ねぎ", "quantity": "1個"},
            {"name": "にんじん", "quantity": "1本"},
        ],
    },
    {
        "type": "hotcook",
        "name": "肉じゃが",
        "menu_num": "0002",
        "category": "主菜",
        "used_ingredients": ["豚バラ肉", "玉ねぎ"],
        "note": "",
    },
]


def _setup_fridge_and_recipes(
    create_ingredient_master: Callable[..., Any],
    create_fridge_item: Callable[..., Any],
    create_hotcook_recipe: Callable[..., Any],
    create_hotcook_recipe_ingredient: Callable[..., Any],
    create_hotcook_recipe_step: Callable[..., Any],
    create_hotcook_recipe_material: Callable[..., Any] | None = None,
) -> tuple[Any, Any, Any]:
    pork = create_ingredient_master(name="豚バラ肉", default_expiry_days=3)
    onion = create_ingredient_master(name="玉ねぎ", default_expiry_days=14)
    carrot = create_ingredient_master(name="にんじん", default_expiry_days=10)
    nira = create_ingredient_master(name="ニラ", default_expiry_days=3)

    create_fridge_item(ingredient_master=pork, quantity_status="full")
    create_fridge_item(ingredient_master=onion, quantity_status="half")
    create_fridge_item(ingredient_master=carrot, quantity_status="little")
    # ニラは冷蔵庫にない → missing_ingredientsに出るべき

    recipe1 = create_hotcook_recipe(code="R0001", name="豚汁", menu_num="0001", category="汁物")
    create_hotcook_recipe_ingredient(recipe=recipe1, ingredient_master=pork)
    create_hotcook_recipe_ingredient(recipe=recipe1, ingredient_master=onion)
    create_hotcook_recipe_ingredient(recipe=recipe1, ingredient_master=nira)
    create_hotcook_recipe_step(recipe=recipe1, step_order=1, text="材料を入れる")
    create_hotcook_recipe_step(recipe=recipe1, step_order=2, text="スタートを押す")
    if create_hotcook_recipe_material:
        create_hotcook_recipe_material(recipe=recipe1, material_order=1, name="豚バラ肉", quantity="200g")
        create_hotcook_recipe_material(recipe=recipe1, material_order=2, name="玉ねぎ", quantity="1個")
        create_hotcook_recipe_material(recipe=recipe1, material_order=3, name="ニラ", quantity="1束")

    recipe2 = create_hotcook_recipe(code="R0002", name="肉じゃが", menu_num="0002", category="主菜")
    create_hotcook_recipe_ingredient(recipe=recipe2, ingredient_master=pork)
    create_hotcook_recipe_ingredient(recipe=recipe2, ingredient_master=onion)

    return pork, onion, carrot


@patch("routers.suggest.create_gemini_client")
def test_suggest_omakase(
    mock_create_gemini: MagicMock,
    client: Any,
    create_ingredient_master: Callable[..., Any],
    create_fridge_item: Callable[..., Any],
    create_hotcook_recipe: Callable[..., Any],
    create_hotcook_recipe_ingredient: Callable[..., Any],
    create_hotcook_recipe_step: Callable[..., Any],
    create_hotcook_recipe_material: Callable[..., Any],
) -> None:
    _setup_fridge_and_recipes(
        create_ingredient_master,
        create_fridge_item,
        create_hotcook_recipe,
        create_hotcook_recipe_ingredient,
        create_hotcook_recipe_step,
        create_hotcook_recipe_material,
    )

    mock_client = MagicMock()
    mock_client.generate_json.return_value = MOCK_GEMINI_RESPONSE
    mock_create_gemini.return_value = mock_client

    res = client.post("/recipe/suggest", json={"mode": "omakase"})
    assert res.status_code == 200
    data = res.json()

    assert len(data["suggestions"]) == 3

    hotcook_item = data["suggestions"][0]
    assert hotcook_item["type"] == "hotcook"
    assert hotcook_item["menu_num"] == "0001"
    assert hotcook_item["category"] == "汁物"
    assert len(hotcook_item["steps"]) == 2
    assert hotcook_item["steps"][0]["text"] == "材料を入れる"
    assert len(hotcook_item["materials"]) == 3
    assert hotcook_item["materials"][0]["name"] == "豚バラ肉"
    assert hotcook_item["materials"][0]["quantity"] == "200g"
    # DBの食材マスタから不足食材を算出（ニラは冷蔵庫にない）
    assert hotcook_item["missing_ingredients"] == ["ニラ"]

    manual_item = data["suggestions"][1]
    assert manual_item["type"] == "manual"
    assert manual_item["category"] == "主菜"
    assert len(manual_item["steps"]) == 3
    assert len(manual_item["materials"]) == 3
    assert manual_item["materials"][0]["name"] == "豚バラ肉"
    assert manual_item["materials"][0]["quantity"] == "200g"
    assert manual_item["materials"][2]["name"] == "にんじん"
    # manualの場合はGeminiのused_ingredientsから算出（全部冷蔵庫にある）
    assert manual_item["missing_ingredients"] == []


@patch("routers.suggest.create_gemini_client")
def test_suggest_ingredient_mode(
    mock_create_gemini: MagicMock,
    client: Any,
    db_session: Any,
    create_ingredient_master: Callable[..., Any],
    create_fridge_item: Callable[..., Any],
    create_hotcook_recipe: Callable[..., Any],
    create_hotcook_recipe_ingredient: Callable[..., Any],
    create_hotcook_recipe_step: Callable[..., Any],
) -> None:
    pork, onion, carrot = _setup_fridge_and_recipes(
        create_ingredient_master,
        create_fridge_item,
        create_hotcook_recipe,
        create_hotcook_recipe_ingredient,
        create_hotcook_recipe_step,
    )

    mock_client = MagicMock()
    mock_client.generate_json.return_value = MOCK_GEMINI_RESPONSE
    mock_create_gemini.return_value = mock_client

    res = client.post(
        "/recipe/suggest",
        json={"mode": "ingredient", "ingredient_master_ids": [pork.id]},
    )
    assert res.status_code == 200

    prompt_call = mock_client.generate_json.call_args[0][0]
    assert "豚バラ肉" in prompt_call


@patch("routers.suggest.create_gemini_client")
def test_suggest_empty_fridge(mock_create_gemini: MagicMock, client: Any) -> None:
    mock_client = MagicMock()
    mock_create_gemini.return_value = mock_client

    res = client.post("/recipe/suggest", json={"mode": "omakase"})
    assert res.status_code == 400
    assert "冷蔵庫に食材がありません" in res.json()["detail"]
    mock_client.generate_json.assert_not_called()


def test_add_shopping(
    client: Any,
    db_session: Any,
    create_ingredient_master: Callable[..., Any],
) -> None:
    create_ingredient_master(name="豚バラ肉", default_expiry_days=3)
    create_ingredient_master(name="玉ねぎ", default_expiry_days=14)

    res = client.post(
        "/recipe/suggest/add-shopping",
        json={"ingredient_names": ["豚バラ肉", "玉ねぎ", "存在しない食材"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["added_count"] == 2

    items = db_session.query(ShoppingItem).all()
    assert len(items) == 2
    assert all(i.source == "recipe" for i in items)


def test_add_shopping_no_duplicate(
    client: Any,
    db_session: Any,
    create_ingredient_master: Callable[..., Any],
    create_shopping_item: Callable[..., Any],
) -> None:
    pork = create_ingredient_master(name="豚バラ肉", default_expiry_days=3)
    create_shopping_item(ingredient_master=pork, source="manual")

    res = client.post(
        "/recipe/suggest/add-shopping",
        json={"ingredient_names": ["豚バラ肉"]},
    )
    assert res.status_code == 200
    assert res.json()["added_count"] == 0

    items = db_session.query(ShoppingItem).all()
    assert len(items) == 1
