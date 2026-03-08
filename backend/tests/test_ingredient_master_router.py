from collections.abc import Callable

from fastapi.testclient import TestClient

from entity.ingredient_master import IngredientMaster


class TestGetIngredients:
    def test_empty(self, client: TestClient) -> None:
        resp = client.get("/api/ingredients/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        create_ingredient_master(name="トマト", default_expiry_days=7)
        create_ingredient_master(name="きゅうり", default_expiry_days=5)
        resp = client.get("/api/ingredients/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_staple_first(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        create_ingredient_master(name="トマト", is_staple=False)
        create_ingredient_master(name="塩", is_staple=True)
        create_ingredient_master(name="きゅうり", is_staple=False)
        resp = client.get("/api/ingredients/")
        names = [d["name"] for d in resp.json()]
        assert names[0] == "塩"


class TestCreateIngredient:
    def test_create(self, client: TestClient) -> None:
        resp = client.post(
            "/api/ingredients/",
            json={"name": "トマト", "default_expiry_days": 7, "is_staple": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "トマト"
        assert data["default_expiry_days"] == 7
        assert data["is_staple"] is False
        assert "id" in data

    def test_duplicate_name(
        self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]
    ) -> None:
        create_ingredient_master(name="トマト")
        resp = client.post(
            "/api/ingredients/",
            json={"name": "トマト", "default_expiry_days": 7},
        )
        assert resp.status_code == 409


class TestUpdateIngredient:
    def test_update_staple(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        master = create_ingredient_master(name="トマト", is_staple=False)
        resp = client.patch(f"/api/ingredients/{master.id}", json={"is_staple": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_staple"] is True

    def test_update_expiry(self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]) -> None:
        master = create_ingredient_master(name="トマト", default_expiry_days=7)
        resp = client.patch(f"/api/ingredients/{master.id}", json={"default_expiry_days": 14})
        assert resp.status_code == 200
        assert resp.json()["default_expiry_days"] == 14

    def test_partial_update(
        self, client: TestClient, create_ingredient_master: Callable[..., IngredientMaster]
    ) -> None:
        master = create_ingredient_master(name="トマト", default_expiry_days=7, is_staple=False)
        resp = client.patch(f"/api/ingredients/{master.id}", json={"is_staple": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_staple"] is True
        assert data["default_expiry_days"] == 7

    def test_not_found(self, client: TestClient) -> None:
        resp = client.patch("/api/ingredients/9999", json={"is_staple": True})
        assert resp.status_code == 404
