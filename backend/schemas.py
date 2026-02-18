# -------------------------
# Pydantic-схемы для FastAPI
# Используются для сериализации входов/выходов REST API
# -------------------------

from __future__ import annotations

import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic import ConfigDict


# ------- Схема воспоминания -------
class MemorySchema(BaseModel):
    id: str  # ID воспоминания
    description: str  # Описание/текст воспоминания
    emotion: Optional[str] = None  # Связанная эмоция (может быть None)
    timestamp: datetime.datetime  # Время добавления
    model_config = ConfigDict(from_attributes=True)


# ------- Схема плана/задачи -------
class PlanSchema(BaseModel):
    id: str
    title: str
    status: str = "active"  # статус: active/planned/in-progress/completed
    description: Optional[str] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# ------- Схема взаимодействия -------
class InteractionSchema(BaseModel):
    id: str
    partner: Optional[str] = None  # С кем взаимодействие
    description: str
    timestamp: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class EventSchema(BaseModel):
    id: str
    description: str
    timestamp: datetime.datetime
    type: Optional[str] = None  # Тип события, например "message"
    actor_id: Optional[str] = None  # Инициатор
    target_id: Optional[str] = None  # Получатель
    model_config = ConfigDict(from_attributes=True)


# ------- Схема отношения (ребро графа) -------
class RelationSchema(BaseModel):
    source: str  # ID Агента-источника
    target: str  # ID Агента-цели
    affinity: float  # "Степень симпатии" (от -1 до 1)
    label: Optional[str] = None
    strength: float = 1.0
    updated_at: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ------- Полное описание агента -------
class AgentSchema(BaseModel):
    id: str
    name: str
    mood: float
    energy: int
    traits: List[str] = []  # Черты характера (список)
    persona: Optional[str] = None  # Текстовое описание персонажа
    current_task: Optional[str] = None
    memories: List[MemorySchema] = []  # Воспоминания агента
    plans: List[PlanSchema] = []  # Планы агента
    interactions: List[InteractionSchema] = []  # Взаимодействия агента
    model_config = ConfigDict(from_attributes=True)


# ------- Схема создания нового агента (POST) -------
class AgentCreate(BaseModel):
    name: str
    mood: float = 0.5
    energy: int = 80
    traits: List[str] = []
    persona: Optional[str] = None  # Описание персонажа текстом
    current_task: Optional[str] = None


# ------- Схема создания события -------
class EventCreate(BaseModel):
    description: str
    type: Optional[str] = None
    actor_id: Optional[str] = None
    target_id: Optional[str] = None


# ------- Схема отправки сообщения агенту -------
class MessagePayload(BaseModel):
    message: str
    emotion: Optional[str] = None


# ------- Управление симуляцией -------
class SimulationControlRequest(BaseModel):
    action: Optional[str] = Field(None, description="pause | resume")
    speed: Optional[float] = Field(None, ge=0.1, le=10.0)


class SimulationStatus(BaseModel):
    speed: float
    is_paused: bool
    tick_seconds: float


# ------- Аутентификация -------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    registered_time: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


# ------- Group Chat Schemas -------
class GroupChatCreate(BaseModel):
    name: str
    description: str | None = None
    agent_ids: list[str] = []


class GroupChatUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    agent_ids: list[str] | None = None


class GroupChatSchema(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_by_user_id: str
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    agent_ids: list[str] = []

    model_config = ConfigDict(from_attributes=True)
