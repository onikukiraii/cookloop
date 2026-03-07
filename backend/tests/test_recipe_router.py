from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from entity.hotcook_recipe import HotcookRecipe
from entity.hotcook_recipe_ingredient import HotcookRecipeIngredient
from entity.hotcook_recipe_step import HotcookRecipeStep
from entity.ingredient_master import IngredientMaster


def _create_recipe(
    db_session: Session,
    code: str = "R0001",
    name: str = "肉じゃが",
    ingredients: list[IngredientMaster] | None = None,
    steps: list[str] | None = None,
) -> HotcookRecipe:
    recipe = HotcookRecipe(code=code, name=name)
    db_session.add(recipe)
    db_session.flush()

    for master in ingredients or []:
        db_session.add(HotcookRecipeIngredient(recipe_id=recipe.id, ingredient_master_id=master.id))

    for i, text in enumerate(steps or [], 1):
        db_session.add(HotcookRecipeStep(recipe_id=recipe.id, step_order=i, text=text))

    db_session.commit()
    db_session.refresh(recipe)
    return recipe


class TestSearchRecipes:
    def test_search_by_name(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
    ) -> None:
        master = create_ingredient_master(name="じゃがいも")
        _create_recipe(db_session, name="肉じゃが", ingredients=[master])
        _create_recipe(db_session, code="R0002", name="カレー", ingredients=[master])

        res = client.get("/recipes/?q=肉じゃが")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "肉じゃが"
        assert "じゃがいも" in data[0]["ingredient_names"]

    def test_search_by_ingredient(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
    ) -> None:
        tomato = create_ingredient_master(name="トマト")
        potato = create_ingredient_master(name="じゃがいも")
        _create_recipe(db_session, name="トマトスープ", ingredients=[tomato])
        _create_recipe(db_session, code="R0002", name="肉じゃが", ingredients=[potato])

        res = client.get("/recipes/?q=トマト")
        assert res.status_code == 200
        data = res.json()
        names = [r["name"] for r in data]
        assert "トマトスープ" in names

    def test_search_multiple_keywords_and(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
    ) -> None:
        tomato = create_ingredient_master(name="トマト")
        chicken = create_ingredient_master(name="鶏肉")
        potato = create_ingredient_master(name="じゃがいも")
        _create_recipe(db_session, name="トマトチキンカレー", ingredients=[tomato, chicken])
        _create_recipe(db_session, code="R0002", name="トマトスープ", ingredients=[tomato, potato])
        _create_recipe(db_session, code="R0003", name="唐揚げ", ingredients=[chicken])

        # "トマト 鶏肉" → トマトチキンカレーだけヒット
        res = client.get("/recipes/?q=トマト 鶏肉")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "トマトチキンカレー"

    def test_empty_query_returns_all(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        _create_recipe(db_session, name="肉じゃが")
        _create_recipe(db_session, code="R0002", name="カレー")

        res = client.get("/recipes/")
        assert res.status_code == 200
        assert len(res.json()) == 2


class TestGetRecipeDetail:
    def test_get_detail(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
    ) -> None:
        master = create_ingredient_master(name="じゃがいも")
        recipe = _create_recipe(
            db_session,
            name="肉じゃが",
            ingredients=[master],
            steps=["材料を切る", "煮込む"],
        )

        res = client.get(f"/recipes/{recipe.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "肉じゃが"
        assert data["source_url"].endswith("/R0001")
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["name"] == "じゃがいも"
        assert len(data["steps"]) == 2
        assert data["steps"][0]["step_order"] == 1
        assert data["steps"][0]["text"] == "材料を切る"

    def test_not_found(self, client: TestClient) -> None:
        res = client.get("/recipes/9999")
        assert res.status_code == 404
