# バックエンド仕様書

## 構成概要

- DB：MySQL（トランザクションデータの永続化）
- 検索：OpenSearch（食材名の検索・名前揺れの吸収）
- AI：Gemini API（google-generativeai）
- 環境：ローカル（Mac Mini）、Tailscale経由で出先からもアクセス可

### MySQLとOpenSearchの役割分担

```
MySQL       → 在庫・買い物リスト・レシピの永続化（正）
OpenSearch  → ingredient_masterの検索インデックス（MySQLの写し）
```

マスタに食材が追加・更新されたタイミングでOpenSearchにも同期書き込みする。

---

## テーブルスキーマ

### ingredient_master（食材マスタ）

食材の知識を蓄積するキャッシュ。育つほど登録時の摩擦が下がる。

```sql
CREATE TABLE ingredient_master (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  name                VARCHAR(100) NOT NULL UNIQUE,   -- 食材名（正規化済み）
  default_expiry_days INT NOT NULL,                   -- 賞味期限の目安（日数）
  is_staple           BOOLEAN NOT NULL DEFAULT FALSE, -- 定番フラグ（納豆・卵など）
  created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

スクレイピング時に食材マスタを事前投入する。調味料・油脂類はこのテーブルには入れない（condiment_itemsで別管理）。

### fridge_items（冷蔵庫在庫）

今冷蔵庫にある食材の実体。ingredient_masterをFKで参照。

```sql
CREATE TABLE fridge_items (
  id                     INT AUTO_INCREMENT PRIMARY KEY,
  ingredient_master_id   INT NOT NULL,
  expiry_date            DATE NOT NULL,
  quantity_status        ENUM('full', 'half', 'little') NOT NULL DEFAULT 'full',
  registered_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (ingredient_master_id) REFERENCES ingredient_master(id)
);
```

### shopping_list（買い物リスト）

```sql
CREATE TABLE shopping_list (
  id                     INT AUTO_INCREMENT PRIMARY KEY,
  ingredient_master_id   INT NOT NULL,
  source                 ENUM('manual', 'recipe', 'staple_auto') NOT NULL,
    -- manual:     手動追加
    -- recipe:     レシピ提案から追加
    -- staple_auto: 定番フラグで自動追加（残量「少し」になったとき）
  is_checked             BOOLEAN NOT NULL DEFAULT FALSE,
  added_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  checked_at             DATETIME,
  FOREIGN KEY (ingredient_master_id) REFERENCES ingredient_master(id)
);
```

買い物リストは食材（ingredient_master）のみを対象とする。
調味料は買い物リストには含めず、調味料画面で残量「少し」のものを上部にソートすることで対応する。

### hotcook_recipes（ホットクックレシピ）

スクレイピングで取得したレシピ。

```sql
CREATE TABLE hotcook_recipes (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  code        VARCHAR(30) NOT NULL UNIQUE,   -- 例：R4417
  name        VARCHAR(200) NOT NULL,
  menu_num    VARCHAR(10),                   -- 例：0417。nullあり
  image_url   VARCHAR(500),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### hotcook_recipe_ingredients（レシピ食材 中間テーブル）

レシピと食材マスタのN:Nを管理。
スクレイピング時の食材名正規化・調味料除外後のデータを格納。

```sql
CREATE TABLE hotcook_recipe_ingredients (
  id                     INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id              INT NOT NULL,
  ingredient_master_id   INT NOT NULL,
  FOREIGN KEY (recipe_id) REFERENCES hotcook_recipes(id),
  FOREIGN KEY (ingredient_master_id) REFERENCES ingredient_master(id)
);
```

### hotcook_recipe_steps（調理手順）

献立提案時に一緒に表示するための手順。

```sql
CREATE TABLE hotcook_recipe_steps (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  recipe_id   INT NOT NULL,
  step_order  INT NOT NULL,
  text        TEXT NOT NULL,
  FOREIGN KEY (recipe_id) REFERENCES hotcook_recipes(id)
);
```

### condiment_items（調味料在庫）

食材とは別管理。賞味期限・レシピ提案・マスタ参照すべて不要。残量と定番フラグだけで管理する。
基本的に全品目が定番フラグあり（切らしたくない）。

```sql
CREATE TABLE condiment_items (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(100) NOT NULL,
  quantity_status ENUM('full', 'half', 'little') NOT NULL DEFAULT 'full',
  is_staple       BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## fridge_itemsとcondiment_itemsの違い

| | fridge_items | condiment_items |
|---|---|---|
| 賞味期限 | あり | なし |
| レシピ提案に使う | ◯ | ✗ |
| 定番フラグ | 任意 | 基本全部 |
| マスタ参照 | ingredient_master | なし |

---

## テーブルの関連図

```
ingredient_master
  ├── fridge_items          (今冷蔵庫にある食材)
  ├── shopping_list         (買い物リスト)
  └── hotcook_recipe_ingredients
          └── hotcook_recipes
                └── hotcook_recipe_steps

condiment_items             (調味料・独立管理)
```

---

## OpenSearch インデックス設計

### ingredients インデックス

食材名の検索専用。MySQLのingredient_masterと同期する。

```json
{
  "mappings": {
    "properties": {
      "id":      { "type": "integer" },
      "name":    { "type": "text", "analyzer": "kuromoji" },
      "aliases": { "type": "text", "analyzer": "kuromoji" },
      "yomi":    { "type": "text", "analyzer": "kuromoji" }
    }
  }
}
```

ドキュメント例：
```json
{
  "id": 1,
  "name": "にんじん",
  "aliases": ["人参", "ニンジン", "キャロット"],
  "yomi": "にんじん"
}
```

### 検索時の動作

`name`・`aliases`・`yomi` をまとめてマルチマッチ検索し、スコア順で候補を返す。
kuromojiアナライザーにより「人参」→「にんじん」のような表記揺れを吸収する。

```
ユーザー入力：「人参」
  → OpenSearchでマルチマッチ検索
  → "にんじん" がヒット（aliasesに「人参」が含まれるため）
  → MySQL の ingredient_master.id=1 を取得して登録
```

### aliasesの自動生成

ユーザーが手動で入力する必要はない。以下のタイミングでGeminiが自動生成する。

- **スクレイピング時（初期データ）：** 全食材分をバッチ処理で生成・投入
- **マスタ初回登録時（以降の食材）：** 賞味期限推定と同時に生成

ただしGeminiが誤った別名を登録する可能性があるため、確認UIからaliasesを修正できるようにする（豚こまと豚バラを同一扱いにしてしまうケースなど）。

---

## Gemini APIを使うタイミングと処理内容

### ① 食材マスタ初回登録時（賞味期限推定）

マスタにない食材名が入力されたときだけ呼ぶ。キャッシュヒットしたら不要。

**プロンプト例：**
```
以下の食材について、一般的な冷蔵保存での賞味期限の目安（日数）と
表記揺れ・別名のリストを返してください。

食材名：にんじん

JSONのみで返してください。説明文は不要です。
{
  "default_expiry_days": 14,
  "yomi": "にんじん",
  "aliases": ["人参", "ニンジン", "キャロット"]
}
```

返ってきた `aliases` と `yomi` はOpenSearchのingredientsインデックスに投入する。
MySQLのingredient_masterには `name` と `default_expiry_days` のみ保存。

### ② レシピ提案時

冷蔵庫の状態リストを渡して献立を提案させる。
ホットクックレシピはDBから候補を絞った上でGeminiに渡す（全654件をそのまま渡さない）。

**DBからの候補絞り込み：**

```
① fridge_itemsの食材名リストを取得
② hotcook_recipe_ingredientsを使って
   「冷蔵庫の食材を2つ以上含むレシピ」を候補として抽出
③ 候補レシピ（name・menu_num）をGeminiに渡す
```

**プロンプト例：**
```
【冷蔵庫の状態】
- ほうれん草（残量：少し、残り1日）
- 豚バラ肉（残量：たっぷり、残り3日）
- 玉ねぎ（残量：半分、残り7日）
- 牛乳（残量：たっぷり、残り6日）

【ホットクックで作れる候補レシピ】
- No.0212 豚汁
- No.0156 肉じゃが
- No.0417 さけとキャベツの白ワイン蒸し
（※冷蔵庫の食材と一致度が高いものをDBから事前抽出して渡す）

以下の条件で今夜の夕食を3つ提案してください。
- できるだけ多くの食材を使えるレシピを優先する
- 残量「少し」の食材を優先的に消費する
- 残日数が少ない食材を優先する
- ホットクックで作れる場合はメニュー番号を添える
- ホットクックの候補にない場合は手動調理で提案してよい
- 食材が足りない場合は省略・代替を提示してよい

JSONのみで返してください。
[
  {
    "type": "hotcook",
    "name": "豚汁",
    "menu_num": "0212",
    "used_ingredients": ["豚バラ肉", "玉ねぎ", "ほうれん草"],
    "note": "ほうれん草は少量なので仕上げに加える程度で"
  },
  {
    "type": "manual",
    "name": "豚バラとほうれん草の炒め物",
    "menu_num": null,
    "used_ingredients": ["豚バラ肉", "ほうれん草", "玉ねぎ"],
    "note": "ほうれん草が少量のため付け合わせ程度になります",
    "steps": ["玉ねぎを薄切りにする", "豚バラを炒める", "ほうれん草を加えて炒める", "塩こしょうで味を整える"]
  }
]
```

**レスポンスの使い分け：**
- `type: hotcook` → `hotcook_recipe_steps` からDBの手順を引っ張って表示
- `type: manual`  → Geminiのレスポンスの `steps` をそのまま表示

### ③ スクレイピング後処理（初回のみ）

654件分の食材リストを正規化・調味料除外する。詳細はスクレイピング依頼書参照。

---

## 主要なAPIエンドポイント（概念）

| メソッド | パス | 処理 |
|---|---|---|
| GET | /fridge | 冷蔵庫在庫一覧（期限順） |
| POST | /fridge | 食材追加（マスタにない場合はGeminiで推定→マスタ自動登録→冷蔵庫追加） |
| PATCH | /fridge/{id} | 残量更新（定番食材が `little` → 買い物リストに自動追加） |
| DELETE | /fridge/{id} | 使い切り・削除 |
| GET | /ingredient-master | 食材マスタ一覧 |
| GET | /ingredient-master/search?q=xxx | OpenSearch で食材名をインクリメンタルサーチ |
| POST | /ingredient-master | 食材マスタ追加（Geminiで賞味期限推定・aliases生成） |
| PATCH | /ingredient-master/{id} | 食材マスタ編集（定番フラグ切り替え・賞味期限修正など） |
| GET | /condiments | 調味料一覧 |
| POST | /condiments | 調味料追加 |
| PATCH | /condiments/{id} | 残量更新 |
| DELETE | /condiments/{id} | 削除 |
| GET | /shopping | 買い物リスト一覧（未購入のみ返す） |
| POST | /shopping | 手動追加 |
| PATCH | /shopping/{id}/check | チェック → 冷蔵庫に自動登録 |
| DELETE | /shopping/{id} | リストから削除 |
| POST | /recipe/suggest | 献立提案（Gemini呼び出し） |
| POST | /recipe/suggest/add-shopping | 提案レシピの不足食材をリストに追加 |

### エンドポイント補足

#### `GET /shopping`（未購入のみ返す）

購入済みアイテム（`is_checked = TRUE`）はレスポンスに含めない。フロントでは未購入のみ表示する方針のため、APIレベルでフィルタする。購入済みデータは履歴としてDB上には残る。

#### `PATCH /fridge/{id}`（残量更新時の自動追加）

残量を `little` に更新したとき、対象食材の `is_staple = TRUE` であれば `shopping_list` に `source = 'staple_auto'` として自動追加する。既に同一食材が未購入で存在する場合は重複追加しない。

#### `GET /ingredient-master/search`（OpenSearch検索）

フロントの IngredientSelect コンポーネントからインクリメンタルサーチで呼び出される。OpenSearch の `name`・`aliases`・`yomi` をマルチマッチ検索し、スコア順で候補を返す。
