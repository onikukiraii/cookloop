# Frontend

React 19 + TypeScript 5.9 + Vite 7 + Tailwind CSS v4 + shadcn/ui

## セットアップ

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

http://localhost:5173 で開発サーバーが起動する。

## API 型生成

バックエンド API サーバーが起動している状態で実行する:

```bash
npm run generate-api
```

- `src/api/schema.d.ts` - openapi-typescript が生成する型定義（自動生成・編集不可）
- `src/api/constants.ts` - schema.d.ts からの型エイリアス
- `src/api/fetcher.ts` - openapi-fetch を使った型安全な API クライアント + `unwrap` ヘルパー

## コンポーネント追加

shadcn/ui コンポーネントを追加する:

```bash
npx shadcn add <component-name>
```

## テスト

```bash
npm test           # テスト実行
npm run test:watch # ウォッチモード
```

## その他のコマンド

```bash
npm run build   # 本番ビルド (tsc + vite build)
npm run lint    # ESLint
npm run preview # ビルド結果のプレビュー
```
