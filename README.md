# FastAPI App Template

FastAPI + React で作るフルスタック Web アプリケーションのテンプレート

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Frontend**: React 19, TypeScript, Vite 7, Tailwind CSS v4, shadcn/ui
- **Database**: MySQL 8.0, OpenSearch
- **API連携**: openapi-typescript + openapi-fetch（型安全な API クライアント）
- **Tools**: uv, mise, Ruff, mypy, ESLint, Vitest

## Requirements

- [mise](https://mise.jdx.dev/) (Python, Node.js, uv のバージョン管理 & タスクランナー)
- [Docker](https://www.docker.com/) & Docker Compose

## Quick Start

### 1. mise のインストール

```bash
# macOS (Homebrew)
brew install mise
```

### 2. リポジトリをクローン

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 3. ツールのインストール

```bash
mise install
```

Python 3.14、Node.js 22、uv がインストールされます。

### 4. 環境変数の設定

```bash
cp .env.template .env
cp frontend/.env.example frontend/.env
```

必要に応じて `.env` を編集してください。

### 5. Docker Compose で起動

```bash
docker compose up -d
```

以下のサービスが起動します:
- **Frontend**: http://localhost:5173
- **API**: http://localhost:8000
- **MySQL**: localhost:3309
- **OpenSearch**: localhost:9205

### 6. マイグレーション実行

```bash
mise run migrate
```

### 7. API 型生成

API サーバー起動中に実行:

```bash
mise run generate-api
```

## Development

### ローカル開発（Docker なし）

```bash
# バックエンド
mise run dev

# フロントエンド（別ターミナル）
mise run dev:front
```

※ MySQL と OpenSearch は別途起動が必要です。

### コマンド一覧

```bash
mise tasks  # 利用可能なタスク一覧を表示
```

#### バックエンド

| コマンド | 説明 |
|---------|------|
| `mise run dev` | バックエンド開発サーバー起動 |
| `mise run migrate` | マイグレーション実行 |
| `mise run migrate-gen message="add users table"` | マイグレーションファイル生成 |
| `mise run lint` | Lint チェック (Ruff + mypy) |
| `mise run format` | コードフォーマット |

#### フロントエンド

| コマンド | 説明 |
|---------|------|
| `mise run dev:front` | フロントエンド開発サーバー起動 |
| `mise run lint:front` | Lint チェック (ESLint + tsc) |
| `mise run format:front` | ESLint 自動修正 |
| `mise run build:front` | 本番ビルド |
| `mise run test:front` | テスト実行 (Vitest) |
| `mise run generate-api` | OpenAPI → TypeScript 型生成 |

#### 横断

| コマンド | 説明 |
|---------|------|
| `mise run lint:all` | バックエンド + フロントエンド Lint |

### ディレクトリ構成

```
.
├── backend/
│   ├── alembic/        # マイグレーション
│   ├── db/             # DB接続設定
│   ├── docker/         # Dockerfile
│   ├── entity/         # SQLAlchemy モデル
│   ├── routers/        # APIルーター
│   ├── params/         # リクエストパラメータ
│   ├── response/       # レスポンススキーマ
│   └── main.py         # エントリーポイント
├── frontend/
│   ├── docker/         # Dockerfile
│   ├── src/
│   │   ├── api/        # OpenAPI クライアント・型定義
│   │   ├── components/ # UIコンポーネント (shadcn/ui)
│   │   ├── hooks/      # カスタムフック
│   │   ├── layouts/    # レイアウトコンポーネント
│   │   ├── lib/        # ユーティリティ
│   │   ├── pages/      # ページコンポーネント
│   │   └── test/       # テスト基盤
│   └── package.json
├── compose.yaml
├── mise.toml           # ツール & タスク定義
└── .env.template
```

フロントエンドの詳細は [frontend/README.md](frontend/README.md) を参照。

## License

MIT
