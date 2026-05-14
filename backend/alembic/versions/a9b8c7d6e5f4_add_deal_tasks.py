"""Add deal_tasks for per-deal reminders and to-dos.

Revision ID: a9b8c7d6e5f4
Revises: f7a8b9c0d2e1
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deal_tasks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("dealId", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("dueAt", sa.DateTime(), nullable=True),
        sa.Column("isDone", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("createdBy", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["dealId"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["createdBy"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deal_tasks_id"), "deal_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_deal_tasks_dealId"), "deal_tasks", ["dealId"], unique=False)
    op.create_index(op.f("ix_deal_tasks_dueAt"), "deal_tasks", ["dueAt"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_deal_tasks_dueAt"), table_name="deal_tasks")
    op.drop_index(op.f("ix_deal_tasks_dealId"), table_name="deal_tasks")
    op.drop_index(op.f("ix_deal_tasks_id"), table_name="deal_tasks")
    op.drop_table("deal_tasks")
