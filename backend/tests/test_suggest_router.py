from unittest.mock import MagicMock, patch

from entity.shopping_item import ShoppingItem

MOCK_GEMINI_RESPONSE = [
    {
        "type": "hotcook",
        "name": "豚汁",
        "menu_num": "0001",
        "used_ingredients": ["豚バラ肉", "玉ねぎ"],
        "note": "定番の豚汁",
    },
    {
        "type": "manual",
        "name": "野菜炒め",
        "menu_num": None,
        "used_ingredients": ["豚バラ肉", "玉ねぎ", "にんじん"],
        "note": "",
        "steps": ["材料を切る", "炒める", "味付けする"],
    },
    {
        "type": "hotcook",
        "name": "肉じゃが",
        "menu_num": "0002",
        "used_ingredients": ["豚バラ肉", "玉ねぎ"],
        "note": "",
    },
]


def _setup_fridge_and_recipes(
    create_ingredient_master,
    create_fridge_item,
    create_hotcook_recipe,
    create_hotcook_recipe_ingredient,
    create_hotcook_recipe_step,
):
    pork = create_ingredient_master(name="豚バラ肉", default_expiry_days=3)
    onion = create_ingredient_master(name="玉ねぎ", default_expiry_days=14)
    carrot = create_ingredient_master(name="にんじん", default_expiry_days=10)

    create_fridge_item(ingredient_master=pork, quantity_status="full")
    create_fridge_item(ingredient_master=onion, quantity_status="half")
    create_fridge_item(ingredient_master=carrot, quantity_status="little")

    recipe1 = create_hotcook_recipe(code="R0001", name="豚汁", menu_num="0001")
    create_hotcook_recipe_ingredient(recipe=recipe1, ingredient_master=pork)
    create_hotcook_recipe_ingredient(recipe=recipe1, ingredient_master=onion)
    create_hotcook_recipe_step(recipe=recipe1, step_order=1, text="材料を入れる")
    create_hotcook_recipe_step(recipe=recipe1, step_order=2, text="スタートを押す")

    recipe2 = create_hotcook_recipe(code="R0002", name="肉じゃが", menu_num="0002")
    create_hotcook_recipe_ingredient(recipe=recipe2, ingredient_master=pork)
    create_hotcook_recipe_ingredient(recipe=recipe2, ingredient_master=onion)

    return pork, onion, carrot


@patch("routers.suggest.create_gemini_client")
def test_suggest_omakase(
    mock_create_gemini,
    client,
    create_ingredient_master,
    create_fridge_item,
    create_hotcook_recipe,
    create_hotcook_recipe_ingredient,
    create_hotcook_recipe_step,
):
    _setup_fridge_and_recipes(
        create_ingredient_master,
        create_fridge_item,
        create_hotcook_recipe,
        create_hotcook_recipe_ingredient,
        create_hotcook_recipe_step,
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
    assert len(hotcook_item["steps"]) == 2
    assert hotcook_item["steps"][0]["text"] == "材料を入れる"

    manual_item = data["suggestions"][1]
    assert manual_item["type"] == "manual"
    assert len(manual_item["steps"]) == 3


@patch("routers.suggest.create_gemini_client")
def test_suggest_ingredient_mode(
    mock_create_gemini,
    client,
    db_session,
    create_ingredient_master,
    create_fridge_item,
    create_hotcook_recipe,
    create_hotcook_recipe_ingredient,
    create_hotcook_recipe_step,
):
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
def test_suggest_empty_fridge(mock_create_gemini, client):
    mock_client = MagicMock()
    mock_create_gemini.return_value = mock_client

    res = client.post("/recipe/suggest", json={"mode": "omakase"})
    assert res.status_code == 400
    assert "冷蔵庫に食材がありません" in res.json()["detail"]
    mock_client.generate_json.assert_not_called()


def test_add_shopping(
    client,
    db_session,
    create_ingredient_master,
):
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
    client,
    db_session,
    create_ingredient_master,
    create_shopping_item,
):
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
