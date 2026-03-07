# fastapi_app - FastAPI プロジェクトテンプレート

## プロジェクト構成

- `backend/` - FastAPI (Python 3.14, SQLAlchemy, Alembic)
- `frontend/` - React 19 + TypeScript + Vite + Tailwind CSS v4

## 開発コマンド

```bash
mise install              # Python, uv, Node のセットアップ
docker compose up -d      # 全サービス起動 (API:8000, Frontend:5173, MySQL:3309)
mise run migrate          # マイグレーション実行
mise run migrate-gen message="xxx"  # マイグレーション生成
mise run lint             # バックエンド lint (Ruff + mypy)
mise run lint:front       # フロントエンド lint (ESLint + tsc)
mise run lint:all         # 全体 lint
mise run format           # バックエンド フォーマット
mise run format:front     # フロントエンド lint fix
mise run dev              # バックエンド開発サーバー
mise run dev:front        # フロントエンド開発サーバー
mise run test             # バックエンドテスト
mise run test:front       # フロントエンドテスト
mise run test:all         # 全テスト
mise run generate-api     # OpenAPI → TypeScript 型生成 (要 API サーバー起動)
mise run build:front      # フロントエンド本番ビルド
```

## コミット規約

`/commit` スキルを使用すること。
