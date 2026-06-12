"""public note sharing

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-13

"""

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notes", sa.Column("share_token", sa.String(64), nullable=True))
    op.add_column("notes", sa.Column("shared_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_notes_share_token", "notes", ["share_token"], unique=True)
    op.create_index("ix_notes_shared_at", "notes", ["shared_at"])


def downgrade():
    op.drop_index("ix_notes_shared_at", table_name="notes")
    op.drop_index("ix_notes_share_token", table_name="notes")
    op.drop_column("notes", "shared_at")
    op.drop_column("notes", "share_token")
