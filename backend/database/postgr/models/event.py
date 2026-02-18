# --------------------------
# Модель события симуляции
# --------------------------

from __future__ import annotations

import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgr.db import Base


class Event(Base):
    """
    SQLAlchemy модель 'Event':
    Событие симуляции/мира (любое действие, сообщение, событие для ленты/логгера; связь с агентом по actor_id и target_id).
    """

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )  # уид события
    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # текст/описание события
    type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # тип события ("message" и др.)
    actor_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )  # id инициатора
    target_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )  # id получателя (опционально)
    metadata_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # метаданные в формате JSON
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # дата создания события
