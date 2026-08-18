"""add unique username

Revision ID: c4d2a8e91f3b
Revises: 0127b15b7f74
Create Date: 2026-06-24
"""

from alembic import op


revision = "c4d2a8e91f3b"
down_revision = "0127b15b7f74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
