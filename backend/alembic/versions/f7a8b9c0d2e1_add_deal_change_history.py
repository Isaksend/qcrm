"""Add deal_change_history for deal field audit trail.

Revision ID: f7a8b9c0d2e1
Revises: e6f7a8b9c0d1
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d2e1"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deal_change_history",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("deal_id", sa.String(), nullable=False),
        sa.Column("field", sa.String(length=64), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_change_history_deal_id", "deal_change_history", ["deal_id"])
    op.create_index("ix_deal_change_history_field", "deal_change_history", ["field"])
    op.create_index("ix_deal_change_history_changed_at", "deal_change_history", ["changed_at"])


def downgrade() -> None:
    op.drop_index("ix_deal_change_history_changed_at", table_name="deal_change_history")
    op.drop_index("ix_deal_change_history_field", table_name="deal_change_history")
    op.drop_index("ix_deal_change_history_deal_id", table_name="deal_change_history")
    op.drop_table("deal_change_history")
