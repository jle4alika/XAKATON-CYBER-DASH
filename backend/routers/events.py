# ---------------------------------------------------------
# Роутер для управления событиями
# ---------------------------------------------------------

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgr.db import get_session
from backend.database.postgr.models import Agent, Event, User
from backend.schemas import EventCreate, EventSchema
from backend.services.deps import get_current_active_user
from backend.services.realtime import broker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])


def _serialize_event(event: Event) -> EventSchema:
    """Превращает ORM объект события Event в схему для ответа API."""
    return EventSchema(
        id=event.id,
        description=event.description,
        timestamp=event.created_at,
        type=event.type,
        actor_id=event.actor_id,
        target_id=event.target_id,
    )


@router.get("", response_model=List[EventSchema])
async def list_events(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[EventSchema]:
    """
    Получить последние события симуляции (лента, максимум 200 записей).
    """
    # Получаем события только для агентов текущего пользователя
    result = await session.execute(
        select(Event)
        .join(Agent, Event.actor_id == Agent.id)
        .where(Agent.user_id == current_user.id)
        .order_by(Event.created_at)
        .limit(200)
    )
    events = result.scalars().all()
    return [_serialize_event(e) for e in events]


@router.post("", response_model=EventSchema, status_code=201)
async def create_event(
        payload: EventCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> EventSchema:
    """
    Создать кастомное событие симуляции.
    """
    # Проверяем, что указанные агенты принадлежат текущему пользователю
    if payload.actor_id:
        actor = await session.get(Agent, payload.actor_id)
        if not actor or actor.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to actor agent")

    if payload.target_id:
        target = await session.get(Agent, payload.target_id)
        if not target or target.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to target agent")

    event = Event(
        description=payload.description,
        actor_id=payload.actor_id,
        target_id=payload.target_id,
        type=payload.type or "custom",
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    logger.info(
        "Создано пользовательское событие id=%s type=%s actor_id=%s target_id=%s user_id=%s",
        event.id,
        event.type,
        event.actor_id,
        event.target_id,
        current_user.id,
    )

    await broker.broadcast(
        {
            "type": "event_created",
            "data": {
                "id": event.id,
                "description": event.description,
                "timestamp": event.created_at.isoformat(),
            },
        }
    )

    return _serialize_event(event)
