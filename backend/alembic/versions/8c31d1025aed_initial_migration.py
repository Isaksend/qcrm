"""Initial migration

Revision ID: 8c31d1025aed
Revises: 
Create Date: 2026-05-10 16:16:20.269895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c31d1025aed'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("DROP TABLE IF EXISTS sellers"))


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'sellers',
        sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('avatar', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('role', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('dealsWon', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('dealsClosed', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('revenue', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column('conversionRate', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column('activeLeads', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('sellers_pkey'))
    )
    op.create_index(op.f('ix_sellers_name'), 'sellers', ['name'], unique=False)
    op.create_index(op.f('ix_sellers_id'), 'sellers', ['id'], unique=False)
    op.create_index(op.f('ix_sellers_email'), 'sellers', ['email'], unique=True)
