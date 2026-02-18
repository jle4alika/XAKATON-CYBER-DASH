# -----------------------
# Модель агента симуляции
# -----------------------

from __future__ import annotations

import datetime
import uuid
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, Integer, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.database.postgr.models.user import User
    from backend.database.postgr.models.groupchat import GroupChat

from backend.database.postgr.db import Base

# Import group chat association table
from backend.database.postgr.models.groupchat import group_chat_agents


class Agent(Base):
    """
    SQLAlchemy модель 'Agent':
    1 агент = 1 запись в этой таблице. Хранит ключевые поведенческие характеристики для симуляции.
    """

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )  # уид-идентификатор агента
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # имя агента
    mood: Mapped[float] = mapped_column(Float, default=0.5)  # настроение 0...1
    energy: Mapped[int] = mapped_column(Integer, default=100)  # "энергия" агента
    traits: Mapped[list] = mapped_column(
        JSON, default=list
    )  # черты характера (список строк)
    # Текстовое описание персоны агента (вместо JSON-структуры).
    persona: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    current_task: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # текущая активность

    # Внешний ключ для связи с пользователем
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="agents")

    # Связь с групповыми чатами
    group_chats: Mapped[list["GroupChat"]] = relationship(
        "GroupChat", secondary=group_chat_agents, back_populates="agents"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # дата создания
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )  # дата обновления

    def mood_color(self) -> str:
        """
        Цвет настроения (для UI): green/yellow/red.
        """
        if self.mood >= 0.7:
            return "green"
        if self.mood >= 0.4:
            return "yellow"
        return "red"
