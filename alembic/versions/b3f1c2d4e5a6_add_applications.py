"""Add applications (анкеты) and application_configs

Revision ID: b3f1c2d4e5a6
Revises: a811db77f8a7
Create Date: 2026-11-17 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f1c2d4e5a6'
down_revision: Union[str, None] = 'a811db77f8a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'application_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.String(length=64), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('color', sa.String(length=20), server_default='#5865F2', nullable=False),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('button_label', sa.String(length=80), server_default='Заполнить анкету', nullable=False),
        sa.Column('questions', sa.JSON(), nullable=False),
        sa.Column('approved_role_id', sa.String(length=64), nullable=True),
        sa.Column('review_channel_id', sa.String(length=64), nullable=True),
        sa.Column('dm_on_decision', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('approve_message', sa.Text(), nullable=False),
        sa.Column('reject_message', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_application_configs_guild_id'), 'application_configs', ['guild_id'], unique=True)

    op.create_table(
        'applications',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('guild_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('user_name', sa.String(length=100), nullable=False),
        sa.Column('user_avatar', sa.String(length=500), nullable=True),
        sa.Column('answers', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('reject_reason', sa.Text(), nullable=True),
        sa.Column('reviewer_id', sa.String(length=64), nullable=True),
        sa.Column('reviewer_name', sa.String(length=100), nullable=True),
        sa.Column('review_channel_id', sa.String(length=64), nullable=True),
        sa.Column('review_message_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_applications_guild_id'), 'applications', ['guild_id'], unique=False)
    op.create_index(op.f('ix_applications_user_id'), 'applications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_applications_user_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_guild_id'), table_name='applications')
    op.drop_table('applications')
    op.drop_index(op.f('ix_application_configs_guild_id'), table_name='application_configs')
    op.drop_table('application_configs')
