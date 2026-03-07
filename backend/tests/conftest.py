import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from collections.abc import Callable, Generator  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from db.session import get_db  # noqa: E402
from entity.base import Base  # noqa: E402
from entity.condiment_item import CondimentItem  # noqa: E402
from entity.fridge_item import FridgeItem  # noqa: E402
from entity.ingredient_master import IngredientMaster  # noqa: E402
from entity.shopping_item import ShoppingItem  # noqa: E402
from entity.user import User  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn: Any, _: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient]:
    def _override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user(db_session: Session) -> Callable[..., User]:
    def _factory(
        name: str = "テスト太郎",
        email: str = "test@example.com",
    ) -> User:
        user = User(name=name, email=email)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _factory


@pytest.fixture()
def create_ingredient_master(db_session: Session) -> Callable[..., IngredientMaster]:
    def _factory(
        name: str = "トマト",
        default_expiry_days: int = 7,
        is_staple: bool = False,
    ) -> IngredientMaster:
        master = IngredientMaster(name=name, default_expiry_days=default_expiry_days, is_staple=is_staple)
        db_session.add(master)
        db_session.commit()
        db_session.refresh(master)
        return master

    return _factory


@pytest.fixture()
def create_fridge_item(db_session: Session) -> Callable[..., FridgeItem]:
    def _factory(
        ingredient_master: IngredientMaster,
        expiry_date: str = "2026-03-14",
        quantity_status: str = "full",
    ) -> FridgeItem:
        from datetime import date

        item = FridgeItem(
            ingredient_master_id=ingredient_master.id,
            expiry_date=date.fromisoformat(expiry_date),
            quantity_status=quantity_status,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        return item

    return _factory


@pytest.fixture()
def create_condiment_item(db_session: Session) -> Callable[..., CondimentItem]:
    def _factory(
        name: str = "醤油",
        quantity_status: str = "full",
        is_staple: bool = True,
    ) -> CondimentItem:
        item = CondimentItem(name=name, quantity_status=quantity_status, is_staple=is_staple)
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        return item

    return _factory


@pytest.fixture()
def create_shopping_item(db_session: Session) -> Callable[..., ShoppingItem]:
    def _factory(
        ingredient_master: IngredientMaster,
        source: str = "manual",
    ) -> ShoppingItem:
        item = ShoppingItem(
            ingredient_master_id=ingredient_master.id,
            source=source,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        return item

    return _factory
