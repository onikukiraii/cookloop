# デザイントークン

cookloop のフロントエンドで使用するデザイントークンの定義。
アプリのコンセプト「冷蔵庫を開けなくても、今夜の献立が決まる」に基づき、食材の新鮮さ・家庭料理の温かさ・日々の食のループを表現する。

## ブランドカラー

### Primary - Herb Green（ハーブグリーン）

食材の新鮮さ、健康的な食生活を象徴するセージグリーン。
アプリ全体のメインカラーとして使用する。

| トークン | OKLCH | 用途 |
|---|---|---|
| `brand-50` | `oklch(0.97 0.01 145)` | 最も薄い背景 |
| `brand-100` | `oklch(0.93 0.03 145)` | カードの薄い背景 |
| `brand-200` | `oklch(0.87 0.06 145)` | ホバー状態の背景 |
| `brand-300` | `oklch(0.79 0.09 145)` | ボーダー、ディバイダー |
| `brand-400` | `oklch(0.70 0.12 145)` | アイコン（非アクティブ） |
| `brand-500` | `oklch(0.60 0.15 145)` | メインカラー、ボタン |
| `brand-600` | `oklch(0.52 0.13 145)` | ホバー時のボタン |
| `brand-700` | `oklch(0.44 0.11 145)` | アクティブ状態 |
| `brand-800` | `oklch(0.37 0.09 145)` | テキスト（強調） |
| `brand-900` | `oklch(0.30 0.07 145)` | テキスト（見出し） |

> Hue 145 はセージやバジルのような落ち着いた緑。鮮やかすぎず、食材の自然な色味に近い。

### Warm - Honey Amber（ハニーアンバー）

家庭料理の温かさ、キッチンの灯りを表現する暖色。
セカンダリカラーとして、CTAやアクセントに使用する。

| トークン | OKLCH | 用途 |
|---|---|---|
| `warm-50` | `oklch(0.97 0.01 80)` | 最も薄い背景 |
| `warm-100` | `oklch(0.93 0.03 80)` | 通知バッジの背景 |
| `warm-200` | `oklch(0.87 0.06 80)` | ハイライト |
| `warm-300` | `oklch(0.80 0.10 80)` | ボーダー |
| `warm-400` | `oklch(0.73 0.14 80)` | アイコン |
| `warm-500` | `oklch(0.65 0.16 80)` | メインカラー |
| `warm-600` | `oklch(0.57 0.14 80)` | ホバー |
| `warm-700` | `oklch(0.49 0.12 80)` | アクティブ |
| `warm-800` | `oklch(0.41 0.10 80)` | テキスト（強調） |
| `warm-900` | `oklch(0.33 0.08 80)` | テキスト（見出し） |

> Hue 80 は蜂蜜やバターのような温かみのある黄色〜琥珀色。

---

## セマンティックカラー

アプリのドメイン固有の意味を持つカラー。

### 鮮度ステータス

冷蔵庫内の食材の賞味期限・鮮度状態を視覚的に伝える。

| トークン | OKLCH | 意味 |
|---|---|---|
| `freshness-safe` | `oklch(0.65 0.17 145)` | 安全（期限まで3日以上） |
| `freshness-warning` | `oklch(0.75 0.16 80)` | 注意（期限まで2日以内） |
| `freshness-danger` | `oklch(0.63 0.22 25)` | 危険（今日・明日が期限） |
| `freshness-expired` | `oklch(0.55 0.20 15)` | 期限切れ |

### 残量ステータス

食材の残量を3段階で表す。

| トークン | OKLCH | 意味 |
|---|---|---|
| `quantity-plenty` | `oklch(0.65 0.17 145)` | たっぷり |
| `quantity-half` | `oklch(0.75 0.16 80)` | 半分 |
| `quantity-low` | `oklch(0.63 0.22 25)` | 少し（定番なら買い物リストへ） |

### 買い物リストセクション

| トークン | OKLCH | 意味 |
|---|---|---|
| `shopping-manual` | `oklch(0.60 0.15 145)` | 手動追加 / レシピ由来 |
| `shopping-auto` | `oklch(0.65 0.16 80)` | 定番フラグによる自動追加 |

### 機能カラー

| トークン | OKLCH | 意味 |
|---|---|---|
| `hotcook` | `oklch(0.63 0.22 25)` | ホットクック対応レシピ（ホットクックの赤） |
| `ai-suggest` | `oklch(0.55 0.15 280)` | AI提案コンテンツ |
| `staple-flag` | `oklch(0.65 0.16 80)` | 定番フラグ |

---

## ニュートラルカラー

shadcn/ui のデフォルトニュートラルをそのまま使用する。
`index.css` の `:root` / `.dark` に定義済みの `--background`, `--foreground`, `--muted` 等を参照。

---

## タイポグラフィ

| トークン | 値 | 用途 |
|---|---|---|
| `font-sans` | `'Noto Sans JP', sans-serif` | 本文全体 |
| `text-xs` | `0.75rem / 1rem` | 補助テキスト、バッジ |
| `text-sm` | `0.875rem / 1.25rem` | 食材名（リスト内） |
| `text-base` | `1rem / 1.5rem` | 本文 |
| `text-lg` | `1.125rem / 1.75rem` | セクション見出し |
| `text-xl` | `1.25rem / 1.75rem` | 画面タイトル |
| `text-2xl` | `1.5rem / 2rem` | 大見出し |

> Tailwind CSS v4 のデフォルトスケールに準拠。カスタム定義は不要。

---

## 角丸（Border Radius）

| トークン | 値 | 用途 |
|---|---|---|
| `radius-sm` | `calc(var(--radius) - 4px)` | バッジ、小ボタン |
| `radius-md` | `calc(var(--radius) - 2px)` | インプット |
| `radius-lg` | `var(--radius)` | カード |
| `radius-xl` | `calc(var(--radius) + 4px)` | モーダル |

> `--radius` のベース値は `0.625rem`。shadcn/ui 準拠。

---

## スペーシング

Tailwind CSS v4 のデフォルトスペーシングスケール（4px ベース）をそのまま使用する。
カスタムスペーシングは定義しない。

---

## カラーの使い分けガイド

### ボタン

| 種類 | 背景 | テキスト |
|---|---|---|
| プライマリ | `brand-500` | white |
| セカンダリ | `warm-500` | white |
| ゴースト | transparent | `foreground` |
| デストラクティブ | `destructive` | white |

### カード

| 状態 | ボーダー | 背景 |
|---|---|---|
| 通常 | `border` | `card` |
| 鮮度：安全 | `freshness-safe` | `brand-50` |
| 鮮度：注意 | `freshness-warning` | `warm-50` |
| 鮮度：危険 | `freshness-danger` | 薄い赤背景 |

### 食材リスト

- 残量インジケーター：`quantity-plenty` / `quantity-half` / `quantity-low` の色でバーやドットを表示
- 定番フラグ：`staple-flag` の色でスターアイコン等を表示

---

## CSS 変数への反映

`frontend/src/index.css` の `@theme inline` ブロック内にコメントアウトされたブランドカラーのテンプレートがある。
実装時にはこれらを有効化し、上記トークンの値で置き換える。

```css
@theme inline {
    /* Brand - Herb Green */
    --color-brand-50: oklch(0.97 0.01 145);
    --color-brand-100: oklch(0.93 0.03 145);
    --color-brand-500: oklch(0.60 0.15 145);
    /* ... */

    /* Warm - Honey Amber */
    --color-warm-50: oklch(0.97 0.01 80);
    --color-warm-500: oklch(0.65 0.16 80);
    /* ... */

    /* Semantic */
    --color-freshness-safe: oklch(0.65 0.17 145);
    --color-freshness-warning: oklch(0.75 0.16 80);
    --color-freshness-danger: oklch(0.63 0.22 25);
    --color-freshness-expired: oklch(0.55 0.20 15);
}
```

Tailwind CSS v4 ではこれらを `bg-brand-500`, `text-warm-800`, `border-freshness-danger` のようにユーティリティクラスとして直接使用できる。
