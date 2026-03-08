from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from entity.fridge_item import FridgeItem
from entity.ingredient_master import IngredientMaster
from entity.shopping_item import ShoppingItem


class TestGetFridgeItems:
    def test_empty(self, client: TestClient) -> None:
        resp = client.get("/api/fridge/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(
        self,
        client: TestClient,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_fridge_item: Callable[..., FridgeItem],
    ) -> None:
        master = create_ingredient_master(name="トマト")
        create_fridge_item(ingredient_master=master, expiry_date="2026-03-10")
        resp = client.get("/api/fridge/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ingredient_name"] == "トマト"


class TestCreateFridgeItem:
    def test_create(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        master = create_ingredient_master(name="トマト")
        resp = client.post(
            "/api/fridge/",
            json={"ingredient_master_id": master.id, "expiry_date": "2026-03-14"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ingredient_name"] == "トマト"
        assert data["expiry_date"] == "2026-03-14"
        assert data["quantity_status"] == "full"

    def test_auto_expiry(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        master = create_ingredient_master(name="トマト", default_expiry_days=7)
        resp = client.post(
            "/api/fridge/",
            json={"ingredient_master_id": master.id},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["expiry_date"] is not None

    def test_invalid_master(self, client: TestClient) -> None:
        resp = client.post(
            "/api/fridge/",
            json={"ingredient_master_id": 9999},
        )
        assert resp.status_code == 404


class TestUpdateFridgeItem:
    def test_update(
        self,
        client: TestClient,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_fridge_item: Callable[..., FridgeItem],
    ) -> None:
        master = create_ingredient_master(name="トマト")
        item = create_fridge_item(ingredient_master=master)
        resp = client.patch(f"/api/fridge/{item.id}", json={"quantity_status": "half"})
        assert resp.status_code == 200
        assert resp.json()["quantity_status"] == "half"

    def test_little_staple_auto_adds_shopping(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_fridge_item: Callable[..., FridgeItem],
    ) -> None:
        master = create_ingredient_master(name="納豆", is_staple=True)
        item = create_fridge_item(ingredient_master=master)
        resp = client.patch(f"/api/fridge/{item.id}", json={"quantity_status": "little"})
        assert resp.status_code == 200
        shopping_items = db_session.query(ShoppingItem).all()
        assert len(shopping_items) == 1
        assert shopping_items[0].ingredient_master_id == master.id
        assert shopping_items[0].source == "staple_auto"

    def test_little_non_staple_no_shopping(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_fridge_item: Callable[..., FridgeItem],
    ) -> None:
        master = create_ingredient_master(name="トマト", is_staple=False)
        item = create_fridge_item(ingredient_master=master)
        resp = client.patch(f"/api/fridge/{item.id}", json={"quantity_status": "little"})
        assert resp.status_code == 200
        shopping_items = db_session.query(ShoppingItem).all()
        assert len(shopping_items) == 0

    def test_little_staple_no_duplicate(
        self,
        client: TestClient,
        db_session: Session,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_fridge_item: Callable[..., FridgeItem],
        create_shopping_item: Callable[..., ShoppingItem],
    ) -> None:
        master = create_ingredient_master(name="納豆", is_staple=True)
        item = create_fridge_item(ingredient_master=master)
        create_shopping_item(ingredient_master=master, source="manual")
        resp = client.patch(f"/api/fridge/{item.id}", json={"quantity_status": "little"})
        assert resp.status_code == 200
        shopping_items = db_session.query(ShoppingItem).all()
        assert len(shopping_items) == 1

    def test_not_found(self, client: TestClient) -> None:
        resp = client.patch("/api/fridge/9999", json={"quantity_status": "half"})
        assert resp.status_code == 404


class TestDeleteFridgeItem:
    def test_delete(
        self,
        client: TestClient,
        create_ingredient_master: Callable[..., IngredientMaster],
        create_fridge_item: Callable[..., FridgeItem],
    ) -> None:
        master = create_ingredient_master(name="トマト")
        item = create_fridge_item(ingredient_master=master)
        resp = client.delete(f"/api/fridge/{item.id}")
        assert resp.status_code == 204

    def test_not_found(self, client: TestClient) -> None:
        resp = client.delete("/api/fridge/9999")
        assert resp.status_code == 404
