"""add api_key column

Revision ID: v2_add_api_key
Revises: v1_initial_schema
Create Date: 2024-07-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "v2_add_api_key"
down_revision = "v1_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("api_key", sa.String(length=255), nullable=True),
    )
    op.create_index(op.f("ix_users_api_key"), "users", ["api_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_api_key"), table_name="users")
    op.drop_column("users", "api_key")
