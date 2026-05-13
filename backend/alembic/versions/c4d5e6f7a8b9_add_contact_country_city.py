"""Add country and city to contacts for geo analytics.

Revision ID: c4d5e6f7a8b9
Revises: 72abde6824ab
Create Date: 2026-05-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "72abde6824ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("country_iso2", sa.String(length=2), nullable=True))
    op.add_column("contacts", sa.Column("city", sa.String(length=128), nullable=True))
    op.create_index("ix_contacts_country_iso2", "contacts", ["country_iso2"], unique=False)
    op.create_index("ix_contacts_city", "contacts", ["city"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contacts_city", table_name="contacts")
    op.drop_index("ix_contacts_country_iso2", table_name="contacts")
    op.drop_column("contacts", "city")
    op.drop_column("contacts", "country_iso2")
