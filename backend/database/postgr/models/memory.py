# ------------------------------------
# Модель воспоминания агента (memory)
# ------------------------------------

from __future__ import annotations

import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgr.db import Base


class Memory(Base):
    """
    SQLAlchemy модель 'Memory':
    Запись о воспоминании агента (эмоция, связанное событие, описание).
    Хранит только метаданные (сам текст — в ChromaDB).
    """

    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )  # уид воспоминания
    agent_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="CASCADE")
    )  # ссылка на агента
    description: Mapped[str] = mapped_column(Text, nullable=False)  # текст/описание
    emotion: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # эмоция (если есть)
    source_event_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )  # id исходного события (если связано)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # дата появления воспоминания
