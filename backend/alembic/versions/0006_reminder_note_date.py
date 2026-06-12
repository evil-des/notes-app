"""store reminder note date

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-12

"""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("note_reminders", sa.Column("note_date", sa.Date(), nullable=True))
    op.execute(
        """
        UPDATE note_reminders
        SET note_date = notes.note_date
        FROM notes
        WHERE notes.id = note_reminders.note_id
        """
    )
    op.execute("DELETE FROM note_reminders WHERE note_date IS NULL")
    op.execute(
        """
        DELETE FROM note_reminders nr
        USING (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY note_id, note_date
                    ORDER BY
                        CASE WHEN status = 'sent' THEN 0 ELSE 1 END,
                        id
                ) AS rn
            FROM note_reminders
        ) ranked
        WHERE nr.id = ranked.id AND ranked.rn > 1
        """
    )
    op.alter_column("note_reminders", "note_date", nullable=False)
    op.drop_constraint("uq_note_reminders_note_scheduled", "note_reminders", type_="unique")
    op.create_unique_constraint(
        "uq_note_reminders_note_date",
        "note_reminders",
        ["note_id", "note_date"],
    )
    op.create_index("ix_note_reminders_note_date", "note_reminders", ["note_date"])


def downgrade():
    op.drop_index("ix_note_reminders_note_date", table_name="note_reminders")
    op.drop_constraint("uq_note_reminders_note_date", "note_reminders", type_="unique")
    op.create_unique_constraint(
        "uq_note_reminders_note_scheduled",
        "note_reminders",
        ["note_id", "scheduled_for"],
    )
    op.drop_column("note_reminders", "note_date")
