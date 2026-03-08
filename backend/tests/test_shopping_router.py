from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from entity.fridge_item import FridgeItem
from entity.ingredient_master import IngredientMaster
from entity.shopping_item import ShoppingItem


class TestGetShoppingItems:
    def test_empty(self, client: TestClient) -> None:
        resp = client.get("/api/shopping/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(
        self,
        client: TestClient,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_shopping_item: Callable[..., ShoppingItem],
    ) -> None:
        master = create_ingredient_master(name="トマト")
        create_shopping_item(ingredient_master=master)
        resp = client.get("/api/shopping/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ingredient_name"] == "トマト"

    def test_excludes_checked(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_shopping_item: Callable[..., ShoppingItem],
    ) -> None:
        master = create_ingredient_master(name="トマト")
        item = create_shopping_item(ingredient_master=master)
        client.patch(f"/api/shopping/{item.id}/check")
        resp = client.get("/api/shopping/")
        assert resp.status_code == 200
        assert resp.json() == []


class TestCreateShoppingItem:
    def test_create(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        master = create_ingredient_master(name="トマト")
        resp = client.post(
            "/api/shopping/",
            json={"ingredient_master_id": master.id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ingredient_name"] == "トマト"
        assert data["source"] == "manual"
        assert data["is_checked"] is False

    def test_invalid_master(self, client: TestClient) -> None:
        resp = client.post(
            "/api/shopping/",
            json={"ingredient_master_id": 9999},
        )
        assert resp.status_code == 404


class TestCheckShoppingItem:
    def test_check(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_shopping_item: Callable[..., ShoppingItem],
    ) -> None:
        master = create_ingredient_master(name="トマト", default_expiry_days=7)
        item = create_shopping_item(ingredient_master=master)
        resp = client.patch(f"/api/shopping/{item.id}/check")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_checked"] is True
        assert data["checked_at"] is not None

        fridge_items = db_session.query(FridgeItem).all()
        assert len(fridge_items) == 1
        assert fridge_items[0].ingredient_master_id == master.id

    def test_not_found(self, client: TestClient) -> None:
        resp = client.patch("/api/shopping/9999/check")
        assert resp.status_code == 404


class TestDeleteShoppingItem:
    def test_delete(
        self,
        client: TestClient,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_shopping_item: Callable[..., ShoppingItem],
    ) -> None:
        master = create_ingredient_master(name="トマト")
        item = create_shopping_item(ingredient_master=master)
        resp = client.delete(f"/api/shopping/{item.id}")
        assert resp.status_code == 204

    def test_not_found(self, client: TestClient) -> None:
        resp = client.delete("/api/shopping/9999")
        assert resp.status_code == 404
