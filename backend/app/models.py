from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    telegram_link_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    telegram_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    reminder_time: Mapped[str] = mapped_column(String(5), default="09:00")
    language: Mapped[str] = mapped_column(String(2), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    notes: Mapped[list["Note"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    reminders: Mapped[list["NoteReminder"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    note_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    share_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    shared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    pinned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped[User] = relationship(back_populates="notes")
    reminders: Mapped[list["NoteReminder"]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )


class NoteReminder(Base):
    __tablename__ = "note_reminders"
    __table_args__ = (UniqueConstraint("note_id", "note_date", name="uq_note_reminders_note_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    note_date: Mapped[date] = mapped_column(Date, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    note: Mapped[Note] = relationship(back_populates="reminders")
    user: Mapped[User] = relationship(back_populates="reminders")


class IntegrationState(Base):
    __tablename__ = "integration_state"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
