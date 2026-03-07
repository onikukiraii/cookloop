---
paths:
  - "frontend/**"
---

# Frontend

React 19 + TypeScript 5.9 + Vite 7 + Tailwind CSS v4

## コマンド

```bash
npm run dev       # 開発サーバー (localhost:5173)
npm run build     # tsc + vite build
npm run lint      # eslint
npm test          # vitest
```

## API 型生成

```bash
npm run generate-api  # OpenAPI スキーマから TypeScript 型を生成
```

- `src/api/schema.d.ts` - openapi-typescript が生成する型定義（自動生成・編集不可）
- `src/api/constants.ts` - schema.d.ts からの型エイリアス
- `src/api/fetcher.ts` - openapi-fetch を使った型安全な API クライアント + `unwrap` ヘルパー
- API サーバー起動中に実行すること（`docker compose up api`）

### 使い方

```ts
// 型のインポート
import type { components } from '@/api/schema'
type ItemResponse = components['schemas']['ItemResponse']

// API 呼び出し
import { api, unwrap } from '@/api/fetcher'
const items = unwrap<ItemResponse[]>(await api.GET('/items/'))
```

## コード規約

- ESLint + react-hooks + react-refresh プラグイン
- Tailwind CSS v4 (@tailwindcss/vite プラグイン)
- shadcn/ui コンポーネント（`src/components/ui/` は自動生成、ESLint対象外）
- `@/` パスエイリアス → `src/`
