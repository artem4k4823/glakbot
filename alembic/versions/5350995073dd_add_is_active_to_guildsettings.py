"""Add is_active to GuildSettings

Revision ID: 5350995073dd
Revises: d1674a5fa136
Create Date: 2026-08-10 07:30:57.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5350995073dd'
down_revision: Union[str, None] = 'd1674a5fa136'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The column is already added in the database, but we keep this for consistency if db is reset
    op.add_column('guild_settings', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('guild_settings', 'is_active')
