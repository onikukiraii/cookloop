"""empty message

Revision ID: 7a101768a178
Revises:
Create Date: 2025-12-27 21:17:20.231258

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "7a101768a178"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
