"""Add core CRM tables (companies, users, contacts, deals, etc.)

Revision ID: b3c4d5e6f7a8
Revises: 8c31d1025aed
Create Date: 2026-05-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "8c31d1025aed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    tables = set(insp.get_table_names())

    if "companies" not in tables:
        op.create_table(
            "companies",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)
        op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=False)

    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("hashed_password", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("company_id", sa.String(), nullable=True),
            sa.Column("is_active", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    if "contacts" not in tables:
        op.create_table(
            "contacts",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("company", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("avatar", sa.String(), nullable=True),
            sa.Column("revenue", sa.Float(), nullable=True),
            sa.Column("lastContact", sa.String(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("companyId", sa.String(), nullable=True),
            sa.Column("telegram_id", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_contacts_email"), "contacts", ["email"], unique=True)
        op.create_index(op.f("ix_contacts_id"), "contacts", ["id"], unique=False)
        op.create_index(op.f("ix_contacts_name"), "contacts", ["name"], unique=False)
        op.create_index(op.f("ix_contacts_telegram_id"), "contacts", ["telegram_id"], unique=True)

    if "deals" not in tables:
        op.create_table(
            "deals",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("leadId", sa.String(), nullable=True),
            sa.Column("contactId", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("stage", sa.String(), nullable=True),
            sa.Column("closedAt", sa.DateTime(), nullable=True),
            sa.Column("userId", sa.String(), nullable=True),
            sa.Column("companyId", sa.String(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_deals_id"), "deals", ["id"], unique=False)
        op.create_index(op.f("ix_deals_stage"), "deals", ["stage"], unique=False)
        op.create_index(op.f("ix_deals_title"), "deals", ["title"], unique=False)

    if "activities" not in tables:
        op.create_table(
            "activities",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=True),
            sa.Column("entityType", sa.String(), nullable=True),
            sa.Column("entityId", sa.String(), nullable=True),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("timestamp", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_activities_id"), "activities", ["id"], unique=False)

    if "notes" not in tables:
        op.create_table(
            "notes",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dealId", sa.String(), nullable=True),
            sa.Column("userId", sa.String(), nullable=True),
            sa.Column("content", sa.String(), nullable=True),
            sa.Column("createdAt", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_notes_dealId"), "notes", ["dealId"], unique=False)
        op.create_index(op.f("ix_notes_id"), "notes", ["id"], unique=False)
        op.create_index(op.f("ix_notes_userId"), "notes", ["userId"], unique=False)

    if "chat_messages" not in tables:
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("contactId", sa.String(), nullable=True),
            sa.Column("dealId", sa.String(), nullable=True),
            sa.Column("senderRole", sa.String(), nullable=True),
            sa.Column("senderId", sa.String(), nullable=True),
            sa.Column("senderName", sa.String(), nullable=True),
            sa.Column("content", sa.String(), nullable=True),
            sa.Column("messageType", sa.String(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_chat_messages_contactId"), "chat_messages", ["contactId"], unique=False)
        op.create_index(op.f("ix_chat_messages_dealId"), "chat_messages", ["dealId"], unique=False)
        op.create_index(op.f("ix_chat_messages_id"), "chat_messages", ["id"], unique=False)

    if "ai_insights" not in tables:
        op.create_table(
            "ai_insights",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("entityType", sa.String(), nullable=True),
            sa.Column("entityId", sa.String(), nullable=True),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("content", sa.String(), nullable=True),
            sa.Column("confidence", sa.Integer(), nullable=True),
            sa.Column("suggestions", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_ai_insights_id"), "ai_insights", ["id"], unique=False)


def downgrade() -> None:
    for table in (
        "ai_insights",
        "chat_messages",
        "notes",
        "activities",
        "deals",
        "contacts",
        "users",
        "companies",
    ):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
