"""
User model for authentication and authorization
"""

import datetime
import uuid
from sqlalchemy import func, ForeignKey
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from backend.database.postgr.db import Base
from backend.database.postgr.models.agent import Agent
from backend.database.postgr.models.groupchat import GroupChat


class User(Base):
    """
    User table for authentication and authorization
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)

    registered_time: Mapped[datetime.datetime] = mapped_column(
        DATETIME, default=func.now()
    )

    last_activity: Mapped[datetime.datetime] = mapped_column(
        DATETIME, default=func.now()
    )

    # Связь с агентами пользователя
    agents: Mapped[List["Agent"]] = relationship("Agent", back_populates="user")

    # Связь с групповыми чатами пользователя
    group_chats: Mapped[List["GroupChat"]] = relationship("GroupChat", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
