# 新しいモデルを作成する手順

例として `Product` モデルを作成する場合の手順。

## 1. エンティティを作成

`entity/product.py` を作成:

```python
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from entity.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

## 2. entity/__init__.py にエクスポートを追加

```python
from entity.base import Base
from entity.product import Product  # 追加
from entity.user import User

__all__ = ["Base", "Product", "User"]  # 追加
```

## 3. マイグレーションファイルを生成

```bash
make migrate-gen
# Migration message: add products table
```

## 4. マイグレーションを実行

```bash
make migrate
```

## 確認

マイグレーション後、MySQLでテーブルが作成されていることを確認:

```bash
docker compose exec db mysql -uroot -ppassword mydatabase -e "SHOW TABLES;"
```

---

## よく使うパターン

### Enum フィールド

文字列ベースの Enum + 日本語ラベルの `@property`:

```python
from enum import Enum

from sqlalchemy import Column, Integer, String

from entity.base import Base


class ProductStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

    @property
    def label(self) -> str:
        return {
            "draft": "下書き",
            "published": "公開中",
            "archived": "アーカイブ",
        }[self.value]
```

`(str, Enum)` にすることで JSON シリアライズ時に文字列として扱われる。

### relationship + cascade

親子関係を持つモデルの設定:

```python
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from entity.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(255), nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")
```

- `cascade="all, delete-orphan"` で親削除時に子も削除
- `back_populates` で双方向参照を設定
