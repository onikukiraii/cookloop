# cookloop バックエンド

冷蔵庫管理 & 献立提案アプリ「cookloop」のバックエンドAPI。

## 技術スタック

- **Python 3.14** / **uv**（パッケージ管理）
- **FastAPI** — API フレームワーク
- **SQLAlchemy** — ORM
- **Alembic** — マイグレーション
- **MySQL 8.0** — データベース
- **OpenSearch** + kuromoji — 食材・レシピの全文検索
- **Gemini 2.5 Flash** — 献立提案AI・賞味期限推定

## ディレクトリ構成

```
backend/
├── entity/              # SQLAlchemy モデル
│   ├── base.py
│   ├── user.py
│   ├── ingredient_master.py
│   ├── fridge_item.py
│   ├── shopping_item.py
│   ├── condiment_item.py
│   ├── hotcook_recipe.py
│   ├── hotcook_recipe_ingredient.py
│   ├── hotcook_recipe_material.py
│   ├── hotcook_recipe_step.py
│   ├── favorite_recipe.py
│   └── enums.py
├── routers/             # API エンドポイント
├── params/              # リクエストスキーマ (Pydantic)
├── response/            # レスポンススキーマ (Pydantic)
├── lib/                 # 外部サービスクライアント
│   ├── gemini.py        # Gemini API クライアント
│   └── opensearch.py    # OpenSearch クライアント
├── db/                  # DB 接続設定
├── alembic/             # マイグレーション
├── tests/               # テスト
├── main.py
└── pyproject.toml
```

## API エンドポイント一覧

すべてのエンドポイントは `/api` プレフィックス付き。

| ルーター | プレフィックス | 概要 |
|---------|--------------|------|
| users | `/api/users` | ユーザー管理 |
| ingredients | `/api/ingredients` | 食材マスタ管理・検索 |
| fridge | `/api/fridge` | 冷蔵庫の食材管理 |
| condiments | `/api/condiments` | 調味料管理 |
| shopping | `/api/shopping` | 買い物リスト |
| recipe | `/api/recipe` | ホットクックレシピ検索・詳細 |
| suggest | `/api/recipe/suggest` | AI 献立提案・不足食材の買い物リスト追加 |
| favorites | `/api/favorites` | レシピお気に入り |

## 外部サービス連携

### Gemini 2.5 Flash

- 献立提案（冷蔵庫の食材から最適な料理を提案）
- 食材マスタの賞味期限推定

### OpenSearch

- 食材検索（kuromoji アナライザーで表記揺れ対応）
- レシピ検索（タイトル・材料からの全文検索）

## 開発コマンド

[CLAUDE.md](../CLAUDE.md) の `mise run` コマンドを参照。

```bash
mise run dev              # 開発サーバー起動
mise run lint             # Ruff + mypy
mise run format           # コード自動整形
mise run test             # テスト実行
mise run migrate          # マイグレーション実行
mise run migrate-gen message="xxx"  # マイグレーション生成
```
