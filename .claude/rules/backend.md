---
paths:
  - "backend/**"
---

# Backend

FastAPI + SQLAlchemy + Alembic / Python 3.14 / パッケージ管理: uv

## ディレクトリ

- `entity/` - SQLAlchemy モデル (`base.py` に Base クラス)
- `routers/` - API エンドポイント
- `params/` - リクエストスキーマ (Pydantic)
- `response/` - レスポンススキーマ (Pydantic)
- `db/` - DB 接続設定
- `alembic/` - マイグレーション
- `tests/` - pytest テスト

## コード規約

- Ruff: line-length=120, select=[E,W,F,I,B,UP]
- mypy: strict モード (disallow_untyped_defs, warn_return_any 等)
- FastAPI の `Depends` パターンは B008 を ignore 済み
- entity で SQLAlchemy Base の misc エラーは ignore 済み

## コマンド

```bash
uv run fastapi dev                    # 開発サーバー
uv run ruff check . && uv run ruff format --check . && uv run mypy .  # lint
uv run pytest -v                      # テスト実行
uv run alembic upgrade head           # migrate
uv run alembic revision --autogenerate -m "xxx"  # migrate 生成
```
