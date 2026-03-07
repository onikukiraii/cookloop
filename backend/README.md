# FastAPI プロジェクト構築手順

このドキュメントは、FastAPI + MySQL + Alembic のプロジェクトをゼロから構築する手順を記載しています。

## 前提条件

- Python 3.11+
- uv (パッケージマネージャー)
- Docker / Docker Compose

## プロジェクト構成

```
backend/
├── docker/
│   └── Dockerfile
├── entity/              # SQLAlchemy モデル（DBテーブル定義）
│   ├── __init__.py
│   ├── base.py
│   └── user.py
├── params/              # リクエストパラメータ（Pydantic）
│   ├── __init__.py
│   └── user.py
├── response/            # レスポンス（Pydantic）
│   ├── __init__.py
│   └── user.py
├── routers/             # APIエンドポイント
│   ├── __init__.py
│   └── user.py
├── db/                  # DB接続設定
│   ├── __init__.py
│   └── session.py
├── alembic/             # マイグレーション
│   ├── env.py
│   └── versions/
├── main.py
├── alembic.ini
└── pyproject.toml
```

---

## 1. プロジェクト初期化

```bash
# ディレクトリ作成
mkdir -p backend && cd backend

# uv でプロジェクト初期化
uv init

# 依存関係追加
uv add fastapi[standard] sqlalchemy pymysql alembic cryptography python-dotenv
```

## 2. 環境変数の設定

### backend/.env.template → backend/.env

```bash
cp .env.template .env
```

```ini
# Database（ホストから接続用）
DATABASE_URL=mysql+pymysql://root:password@localhost:3309/mydatabase

# MySQL
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=mydatabase
```

### プロジェクトルート/.env.template → .env

```bash
cp .env.template .env
```

```ini
# Docker Compose用（コンテナ間通信）
DATABASE_URL=mysql+pymysql://root:password@db:3306/mydatabase

# MySQL
MYSQL_ROOT_PASSWORD=password
MYSQL_DATABASE=mydatabase
```

**注意**: `.env` は `.gitignore` に含まれています。

## 3. Docker 環境構築

### Dockerfile (docker/Dockerfile)

```dockerfile
# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project
COPY . .
RUN uv sync --frozen
```

### compose.yaml (プロジェクトルート)

```yaml
services:
  api:
    build:
      context: ./backend
      dockerfile: docker/Dockerfile
    ports:
      - 8000:8000
    volumes:
      - ./backend:/app
      - /app/.venv
    env_file:
      - .env
    command: ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]
    depends_on:
      - db

  db:
    image: mysql:8.0
    env_file:
      - .env
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
    ports:
      - 3309:3306
    volumes:
      - mysql-data:/var/lib/mysql

volumes:
  mysql-data:
```

## 4. ディレクトリ構成作成

```bash
mkdir -p entity params response routers db docker
touch entity/__init__.py params/__init__.py response/__init__.py routers/__init__.py db/__init__.py
```

## 5. エンティティ（DBモデル）

### entity/base.py

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

### entity/user.py

```python
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from entity.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

### entity/__init__.py

```python
from entity.base import Base
from entity.user import User

__all__ = ["Base", "User"]
```

## 6. Pydantic スキーマ

### params/user.py

```python
from pydantic import BaseModel, EmailStr


class UserCreateParams(BaseModel):
    name: str
    email: EmailStr
```

### response/user.py

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}
```

## 7. DB接続設定

### db/session.py

```python
import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 8. ルーター（API エンドポイント）

### routers/user.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.session import get_db
from entity.user import User
from params.user import UserCreateParams
from response.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=UserResponse)
def create_user(params: UserCreateParams, db: Session = Depends(get_db)):
    user = User(name=params.name, email=params.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

## 9. メインアプリケーション

### main.py

```python
from fastapi import FastAPI

from routers.user import router as user_router

app = FastAPI()
app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## 10. Alembic セットアップ

```bash
# 初期化
uv run alembic init alembic
```

### alembic/env.py の編集

環境変数から DB URL を取得するように変更：

```python
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from entity import Base

target_metadata = Base.metadata

DATABASE_URL = os.environ["DATABASE_URL"]


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### マイグレーション実行

```bash
# マイグレーションファイル生成
uv run alembic revision --autogenerate -m "create users table"

# マイグレーション実行
uv run alembic upgrade head
```

## 11. Makefile（オプション）

```makefile
include .env
.EXPORT_ALL_VARIABLES:

.PHONY: migrate migrate-gen lint format

migrate:
	cd backend && uv run alembic upgrade head

migrate-gen:
	@read -p "Migration message: " msg; \
	cd backend && uv run alembic revision --autogenerate -m "$$msg"

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .

format:
	cd backend && uv run ruff check --fix . && uv run ruff format .
```

## 12. Linter / 型チェック導入（ruff, mypy）

### インストール

```bash
cd backend
uv add --dev ruff mypy
```

### pyproject.toml に設定を追加

```toml
[tool.ruff]
target-version = "py311"
line-length = 120

[tool.ruff.format]
docstring-code-format = true

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = [
    "B008",  # function call in default argument (FastAPI Depends pattern)
]

[tool.ruff.lint.per-file-ignores]
"alembic/env.py" = ["E402"]  # module level import not at top (alembic structure)

[tool.mypy]
python_version = "3.13"
mypy_path = "."
explicit_package_bases = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "entity.*"
disable_error_code = ["misc"]  # SQLAlchemy Base subclass issue
```

### mypy 設定の解説

| 設定 | 説明 |
|------|------|
| `python_version` | 対象のPythonバージョン |
| `mypy_path` | モジュール検索パス（`.`でカレントディレクトリ） |
| `explicit_package_bases` | パッケージルートを明示的に指定 |
| `warn_return_any` | `Any`型を返す関数に警告 |
| `warn_unused_configs` | 未使用の設定に警告 |
| `disallow_untyped_defs` | 型アノテーションのない関数定義を禁止 |
| `disallow_incomplete_defs` | 部分的な型アノテーションを禁止 |
| `check_untyped_defs` | 型アノテーションのない関数も型チェック |
| `disallow_untyped_decorators` | 型のないデコレータを禁止 |
| `no_implicit_optional` | 暗黙の`Optional`を禁止（`None`デフォルト時） |
| `warn_redundant_casts` | 不要なキャストに警告 |
| `warn_unused_ignores` | 未使用の`# type: ignore`に警告 |
| `warn_no_return` | 戻り値がない関数に警告 |
| `warn_unreachable` | 到達不能コードに警告 |
| `ignore_missing_imports` | 型スタブのないライブラリのimportエラーを無視 |

#### overrides セクション

```toml
[[tool.mypy.overrides]]
module = "entity.*"
disable_error_code = ["misc"]
```

SQLAlchemyの`declarative_base()`が返す`Base`は型が`Any`になるため、サブクラス化すると`misc`エラーが発生する。`entity`モジュールではこのエラーを無視する設定。

### Dockerでは本番用依存のみインストール

`docker/Dockerfile` で `--no-dev` を指定：

```dockerfile
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
```

### 実行方法

```bash
# チェックのみ
make lint

# 自動修正
make format
```

### VS Code 設定（リポジトリルートから開く場合）

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "mypy-type-checker.cwd": "${workspaceFolder}/backend",
  "mypy-type-checker.args": ["--config-file=${workspaceFolder}/backend/pyproject.toml"]
}
```

## 13. GitHub Actions CI

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.13

      - name: Install dependencies
        run: uv sync --dev

      - name: Run ruff check
        run: uv run ruff check .

      - name: Run ruff format check
        run: uv run ruff format --check .

      - name: Run mypy
        run: uv run mypy .
```

---

## 起動方法

```bash
# Docker で起動
docker compose up -d

# API ドキュメント
open http://localhost:8000/docs
```

## よく使うコマンド

| コマンド | 説明 |
|---------|------|
| `docker compose up -d` | 全サービス起動 |
| `docker compose down` | 停止 |
| `docker compose logs -f api` | ログ表示 |
| `make migrate` | マイグレーション実行 |
| `make migrate-gen` | マイグレーションファイル生成 |
| `make lint` | Linter / 型チェック実行 |
| `make format` | コード自動整形 |

## 注意事項

- Docker 内からは `db:3306`、ホストからは `localhost:3309` でDB接続
- `.venv` はホストとコンテナで共有しない（`/app/.venv` で上書き）
- 新しいエンティティを追加したら `entity/__init__.py` にインポートを追加
