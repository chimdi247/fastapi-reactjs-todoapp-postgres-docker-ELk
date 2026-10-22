"""Add users table

Revision ID: 8b1d2f6c4a90
Revises: 30c439a3a2b1
Create Date: 2026-10-20 00:00:00.000000

Keep in sync with docker/postgres/init/01-schema.sql (which stamps this revision).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b1d2f6c4a90'
down_revision: Union[str, Sequence[str], None] = '30c439a3a2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=32), server_default='user', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email', name='uq_users_email'),
    sa.CheckConstraint('email = lower(email)', name='ck_users_email_lowercase'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
