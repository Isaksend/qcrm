"""Add deal_tasks.assignedUserId for executor / notifications.

Revision ID: c2d3e4f5a6b7
Revises: b0c9d8e7f6a5
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b0c9d8e7f6a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("deal_tasks", sa.Column("assignedUserId", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_deal_tasks_assigned_user",
        "deal_tasks",
        "users",
        ["assignedUserId"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_deal_tasks_assignedUserId"), "deal_tasks", ["assignedUserId"], unique=False)

    bind = op.get_bind()
    # В PostgreSQL без кавычек идентификаторы становятся lower-case — нужны кавычки для camelCase.
    bind.execute(
        sa.text(
            """
            UPDATE deal_tasks
            SET "assignedUserId" = (
                SELECT COALESCE(d."userId", deal_tasks."createdBy")
                FROM deals d
                WHERE d.id = deal_tasks."dealId"
            )
            WHERE "assignedUserId" IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_deal_tasks_assignedUserId"), table_name="deal_tasks")
    op.drop_constraint("fk_deal_tasks_assigned_user", "deal_tasks", type_="foreignkey")
    op.drop_column("deal_tasks", "assignedUserId")
