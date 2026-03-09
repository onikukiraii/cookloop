"""integrate condiments into ingredient_master

Revision ID: a1b2c3d4e5f6
Revises: bb6e6685c83d
Create Date: 2026-03-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "bb6e6685c83d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. ingredient_master に category カラム追加
    op.add_column(
        "ingredient_master",
        sa.Column("category", sa.String(20), nullable=False, server_default="ingredient"),
    )

    # 2. condiment_items に ingredient_master_id FK 追加
    op.add_column(
        "condiment_items",
        sa.Column("ingredient_master_id", sa.Integer(), sa.ForeignKey("ingredient_master.id"), nullable=True),
    )

    # 3. データ移行: 既存 condiment_items → IngredientMaster に category='condiment' で登録
    conn = op.get_bind()

    # 既存の condiment_items を取得
    condiments = conn.execute(sa.text("SELECT id, name FROM condiment_items")).fetchall()

    for condiment_id, condiment_name in condiments:
        # 同名の IngredientMaster があるか確認
        existing = conn.execute(
            sa.text("SELECT id FROM ingredient_master WHERE name = :name"),
            {"name": condiment_name},
        ).fetchone()

        if existing:
            master_id = existing[0]
            # 既存のものを condiment カテゴリに更新
            conn.execute(
                sa.text("UPDATE ingredient_master SET category = 'condiment' WHERE id = :id"),
                {"id": master_id},
            )
        else:
            # 新規作成
            conn.execute(
                sa.text(
                    "INSERT INTO ingredient_master (name, default_expiry_days, is_staple, category) "
                    "VALUES (:name, 365, :is_staple, 'condiment')"
                ),
                {"name": condiment_name, "is_staple": True},
            )
            result = conn.execute(
                sa.text("SELECT id FROM ingredient_master WHERE name = :name"),
                {"name": condiment_name},
            ).fetchone()
            master_id = result[0] if result else None

        # condiment_items に FK を紐づけ
        if master_id is not None:
            conn.execute(
                sa.text("UPDATE condiment_items SET ingredient_master_id = :mid WHERE id = :cid"),
                {"mid": master_id, "cid": condiment_id},
            )


def downgrade() -> None:
    op.drop_column("condiment_items", "ingredient_master_id")
    op.drop_column("ingredient_master", "category")
