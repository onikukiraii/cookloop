from collections.abc import Callable

from fastapi.testclient import TestClient

from entity.condiment_item import CondimentItem


class TestGetCondiments:
    def test_empty(self, client: TestClient) -> None:
        resp = client.get("/api/condiments/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(self, client: TestClient, create_condiment_item: Callable[..., CondimentItem]) -> None:
        create_condiment_item(name="醤油")
        create_condiment_item(name="味噌")
        resp = client.get("/api/condiments/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_sorted_by_quantity(self, client: TestClient, create_condiment_item: Callable[..., CondimentItem]) -> None:
        create_condiment_item(name="醤油", quantity_status="full")
        create_condiment_item(name="味噌", quantity_status="little")
        create_condiment_item(name="酢", quantity_status="half")
        resp = client.get("/api/condiments/")
        data = resp.json()
        assert data[0]["name"] == "味噌"
        assert data[1]["name"] == "酢"
        assert data[2]["name"] == "醤油"


class TestCreateCondiment:
    def test_create(self, client: TestClient) -> None:
        resp = client.post(
            "/api/condiments/",
            json={"name": "醤油"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "醤油"
        assert data["quantity_status"] == "full"
        assert data["is_staple"] is True


class TestUpdateCondiment:
    def test_update(self, client: TestClient, create_condiment_item: Callable[..., CondimentItem]) -> None:
        item = create_condiment_item(name="醤油")
        resp = client.patch(f"/api/condiments/{item.id}", json={"quantity_status": "little"})
        assert resp.status_code == 200
        assert resp.json()["quantity_status"] == "little"

    def test_not_found(self, client: TestClient) -> None:
        resp = client.patch("/api/condiments/9999", json={"quantity_status": "half"})
        assert resp.status_code == 404


class TestDeleteCondiment:
    def test_delete(self, client: TestClient, create_condiment_item: Callable[..., CondimentItem]) -> None:
        item = create_condiment_item(name="醤油")
        resp = client.delete(f"/api/condiments/{item.id}")
        assert resp.status_code == 204

    def test_not_found(self, client: TestClient) -> None:
        resp = client.delete("/api/condiments/9999")
        assert resp.status_code == 404
