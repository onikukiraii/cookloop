from collections.abc import Callable

from fastapi.testclient import TestClient

from entity.user import User


class TestGetUsers:
    def test_get_users_empty(self, client: TestClient) -> None:
        resp = client.get("/users/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_users_with_data(self, client: TestClient, create_user: Callable[..., User]) -> None:
        create_user(name="田中太郎", email="tanaka@example.com")
        create_user(name="鈴木花子", email="suzuki@example.com")
        resp = client.get("/users/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "田中太郎"
        assert data[1]["name"] == "鈴木花子"


class TestCreateUser:
    def test_create_user(self, client: TestClient) -> None:
        resp = client.post(
            "/users/",
            json={"name": "新規ユーザー", "email": "new@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "新規ユーザー"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_create_user_duplicate_email(self, client: TestClient, create_user: Callable[..., User]) -> None:
        create_user(name="既存", email="dup@example.com")
        resp = client.post(
            "/users/",
            json={"name": "重複", "email": "dup@example.com"},
        )
        assert resp.status_code == 409
