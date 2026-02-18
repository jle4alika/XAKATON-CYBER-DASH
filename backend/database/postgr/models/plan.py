# --------------------------------------
# Модель задачи/плана для агента (Plan)
# --------------------------------------

from __future__ import annotations

import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgr.db import Base


class Plan(Base):
    """
    SQLAlchemy модель 'Plan':
    План/цель/задача, поставленная агенту.
    Выполняется самим агентом (agent_id).
    """

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )  # уид задачи
    agent_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="CASCADE")
    )  # агент, владелец
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # Краткое название
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Описание/детали
    status: Mapped[str] = mapped_column(String(64), default="active")  # Статус
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # Дата добавления
