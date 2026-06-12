"""telegram reminders

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-12

"""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("telegram_chat_id", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("telegram_link_token", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "telegram_notifications_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )
    op.create_index("ix_users_telegram_chat_id", "users", ["telegram_chat_id"])
    op.create_index(
        "ix_users_telegram_link_token",
        "users",
        ["telegram_link_token"],
        unique=True,
    )

    op.create_table(
        "note_reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("note_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("note_id", "scheduled_for", name="uq_note_reminders_note_scheduled"),
    )
    op.create_index("ix_note_reminders_note_id", "note_reminders", ["note_id"])
    op.create_index("ix_note_reminders_user_id", "note_reminders", ["user_id"])
    op.create_index("ix_note_reminders_scheduled_for", "note_reminders", ["scheduled_for"])
    op.create_index("ix_note_reminders_status", "note_reminders", ["status"])

    op.create_table(
        "integration_state",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("name"),
    )


def downgrade():
    op.drop_table("integration_state")
    op.drop_index("ix_note_reminders_status", table_name="note_reminders")
    op.drop_index("ix_note_reminders_scheduled_for", table_name="note_reminders")
    op.drop_index("ix_note_reminders_user_id", table_name="note_reminders")
    op.drop_index("ix_note_reminders_note_id", table_name="note_reminders")
    op.drop_table("note_reminders")
    op.drop_index("ix_users_telegram_link_token", table_name="users")
    op.drop_index("ix_users_telegram_chat_id", table_name="users")
    op.drop_column("users", "timezone")
    op.drop_column("users", "telegram_notifications_enabled")
    op.drop_column("users", "telegram_link_token")
    op.drop_column("users", "telegram_chat_id")
