"""user language setting

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-12

"""

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("language", sa.String(length=2), nullable=False, server_default="en"),
    )


def downgrade():
    op.drop_column("users", "language")
