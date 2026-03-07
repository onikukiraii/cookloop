<p align="center">
  <img src="frontend/public/logo.svg" alt="CookLoop" width="240">
</p>

高山家の主婦業を楽にするために作った個人用アプリ。

冷蔵庫の在庫と賞味期限を管理する
ホットクック公式レシピのデータをいれて、冷蔵庫の中身から Gemini が「今夜これ作れるよ」とホットクックのメニュー番号付きで提案してくれる。無くなりそうな食材は自動で買い物リストに入れる
このループをCookLoopと呼ぶ

## セットアップ

```bash
mise install                # Python, Node.js, uv のインストール
cp .env.template .env       # 環境変数の設定
docker compose up -d        # 全サービス起動
mise run migrate            # マイグレーション実行
```

起動したら http://localhost:5173 (フロント) と http://localhost:8000/docs (API) が使える。

## 開発

```bash
mise run dev          # バックエンド開発サーバー
mise run dev:front    # フロントエンド開発サーバー
mise run lint:all     # 全体 lint
mise run test:all     # 全テスト
mise tasks            # コマンド一覧
```

## リポジトリの構成

```
backend/          FastAPI + SQLAlchemy + Alembic
frontend/         React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui
docs/
  00_core.md      体験ビジョン・アプリの全体像
  01_backend.md   バックエンド仕様書 (テーブル設計・API・Gemini連携)
compose.yaml      Docker Compose (API, Frontend, MySQL, OpenSearch)
```
