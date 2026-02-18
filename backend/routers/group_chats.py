# ---------------------------------------------------------
# Роутер для управления групповыми чатами
# ---------------------------------------------------------

import logging
import json
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.chrome.db import memory_store
from backend.database.postgr.db import get_session
from backend.database.postgr.models import Agent, Event, Memory, GroupChat
from backend.database.postgr.models.groupchat import group_chat_agents
from backend.database.postgr.models import User
from backend.schemas import (
    GroupChatCreate,
    GroupChatSchema,
    GroupChatUpdate,
    EventSchema,
    MessagePayload,
)
from backend.services.deps import get_current_active_user
from backend.services.realtime import broker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/group-chats", tags=["group-chats"])


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


@router.post("", response_model=GroupChatSchema, status_code=201)
async def create_group_chat(
        payload: GroupChatCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> GroupChatSchema:
    """
    Создать новый групповой чат.
    """
    # Проверяем, что указанные агенты принадлежат текущему пользователю
    if payload.agent_ids:
        result = await session.execute(
            select(Agent).where(
                Agent.id.in_(payload.agent_ids),
                Agent.user_id == current_user.id
            )
        )
        valid_agents = result.scalars().all()
        valid_agent_ids = [str(agent.id) for agent in valid_agents]

        # Проверяем, что все указанные агенты существуют и принадлежат пользователю
        invalid_agent_ids = set(payload.agent_ids) - set(valid_agent_ids)
        if invalid_agent_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Agents not found or don't belong to user: {invalid_agent_ids}"
            )
    else:
        valid_agent_ids = []

    # Создаем групповой чат
    group_chat = GroupChat(
        name=payload.name,
        description=payload.description,
        created_by_user_id=current_user.id
    )

    session.add(group_chat)
    # flush, чтобы получить ID чата без коммита
    await session.flush()

    # Явно создаём связи в таблице group_chat_agents,
    # приводя строковые id агентов к UUID
    for agent_id in valid_agent_ids:
        await session.execute(
            insert(group_chat_agents).values(
                group_chat_id=group_chat.id,
                agent_id=uuid.UUID(agent_id),
            )
        )

    await session.commit()
    await session.refresh(group_chat)
    logger.info(
        "Создан групповой чат id=%s name=%s user_id=%s, количество агентов=%d",
        group_chat.id,
        group_chat.name,
        current_user.id,
        len(valid_agent_ids),
    )

    # Возвращаем переданные agent_ids (они уже провалидированы)
    return GroupChatSchema(
        id=str(group_chat.id),
        name=group_chat.name,
        description=group_chat.description,
        created_by_user_id=str(group_chat.created_by_user_id),
        is_active=group_chat.is_active,
        created_at=group_chat.created_at,
        updated_at=group_chat.updated_at,
        agent_ids=valid_agent_ids
    )


@router.get("", response_model=List[GroupChatSchema])
async def list_group_chats(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[GroupChatSchema]:
    """
    Получить список всех групповых чатов пользователя.
    """
    result = await session.execute(
        select(GroupChat).where(GroupChat.created_by_user_id == current_user.id)
    )
    group_chats = result.scalars().all()

    # Для каждой группы получаем список агентов через таблицу связей,
    # чтобы не зависеть от ORM relationship и типов колонок
    response_chats = []
    for group_chat in group_chats:
        agent_rows = await session.execute(
            select(group_chat_agents.c.agent_id).where(
                group_chat_agents.c.group_chat_id == group_chat.id
            )
        )
        agent_ids = [str(row[0]) for row in agent_rows.fetchall()]

        response_chats.append(
            GroupChatSchema(
                id=str(group_chat.id),
                name=group_chat.name,
                description=group_chat.description,
                created_by_user_id=str(group_chat.created_by_user_id),
                is_active=group_chat.is_active,
                created_at=group_chat.created_at,
                updated_at=group_chat.updated_at,
                agent_ids=agent_ids
            )
        )

    return response_chats


@router.get("/{group_chat_id}", response_model=GroupChatSchema)
async def get_group_chat(
        group_chat_id: str,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> GroupChatSchema:
    """
    Получить информацию о конкретном групповом чате.
    """
    group_chat = await session.get(GroupChat, group_chat_id)
    if not group_chat:
        raise HTTPException(status_code=404, detail="Group chat not found")

    # Проверяем, что чат принадлежит текущему пользователю
    if group_chat.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Получаем агентов в чате через таблицу связей
    agent_rows = await session.execute(
        select(group_chat_agents.c.agent_id).where(
            group_chat_agents.c.group_chat_id == group_chat.id
        )
    )
    agent_ids = [str(row[0]) for row in agent_rows.fetchall()]

    return GroupChatSchema(
        id=str(group_chat.id),
        name=group_chat.name,
        description=group_chat.description,
        created_by_user_id=str(group_chat.created_by_user_id),
        is_active=group_chat.is_active,
        created_at=group_chat.created_at,
        updated_at=group_chat.updated_at,
        agent_ids=agent_ids
    )


@router.put("/{group_chat_id}", response_model=GroupChatSchema)
async def update_group_chat(
        group_chat_id: str,
        payload: GroupChatUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> GroupChatSchema:
    """
    Обновить информацию о групповом чате.
    """
    group_chat = await session.get(GroupChat, group_chat_id)
    if not group_chat:
        raise HTTPException(status_code=404, detail="Group chat not found")

    # Проверяем, что чат принадлежит текущему пользователю
    if group_chat.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Обновляем поля
    if payload.name is not None:
        group_chat.name = payload.name
    if payload.description is not None:
        group_chat.description = payload.description

    # Обработка изменения списка агентов
    if payload.agent_ids is not None:
        # Проверяем, что все указанные агенты принадлежат текущему пользователю
        valid_agents = []
        if payload.agent_ids:
            result = await session.execute(
                select(Agent).where(
                    Agent.id.in_(payload.agent_ids),
                    Agent.user_id == current_user.id
                )
            )
            valid_agents = result.scalars().all()
            valid_agent_ids = [str(agent.id) for agent in valid_agents]

            # Проверяем, что все указанные агенты существуют и принадлежат пользователю
            invalid_agent_ids = set(payload.agent_ids) - set(valid_agent_ids)
            if invalid_agent_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agents not found or don't belong to user: {invalid_agent_ids}"
                )
        else:
            valid_agent_ids = []

        # Полностью пересоздаём связи в таблице group_chat_agents
        await session.execute(
            delete(group_chat_agents).where(
                group_chat_agents.c.group_chat_id == group_chat.id
            )
        )
        for agent_id in valid_agent_ids:
            await session.execute(
                insert(group_chat_agents).values(
                    group_chat_id=group_chat.id,
                    agent_id=uuid.UUID(agent_id),
                )
            )

    await session.commit()
    await session.refresh(group_chat)
    logger.info("Групповой чат обновлён id=%s user_id=%s", group_chat.id, current_user.id)

    # Получаем актуальный список агентов через таблицу связей
    agent_rows = await session.execute(
        select(group_chat_agents.c.agent_id).where(
            group_chat_agents.c.group_chat_id == group_chat.id
        )
    )
    agent_ids = [str(row[0]) for row in agent_rows.fetchall()]

    return GroupChatSchema(
        id=str(group_chat.id),
        name=group_chat.name,
        description=group_chat.description,
        created_by_user_id=str(group_chat.created_by_user_id),
        is_active=group_chat.is_active,
        created_at=group_chat.created_at,
        updated_at=group_chat.updated_at,
        agent_ids=agent_ids
    )


@router.delete("/{group_chat_id}", status_code=204)
async def delete_group_chat(
        group_chat_id: str,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Удалить групповой чат.
    """
    group_chat = await session.get(GroupChat, group_chat_id)
    if not group_chat:
        raise HTTPException(status_code=404, detail="Group chat not found")

    # Проверяем, что чат принадлежит текущему пользователю
    if group_chat.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Удаляем чат
    await session.delete(group_chat)
    await session.commit()
    logger.info("Групповой чат удалён id=%s user_id=%s", group_chat_id, current_user.id)

    # Также нужно удалить связи в таблице group_chat_agents
    # Доработка требуется
    return None


@router.post("/{group_chat_id}/message", response_model=List[EventSchema])
async def send_message_to_group_chat(
        group_chat_id: str,
        payload: MessagePayload,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[EventSchema]:
    """
    Отправить сообщение сразу всем агентам в выбранном групповом чате.
    Для каждого агента создается Event + Memory, чтобы они учитывали это в своем поведении.
    """
    group_chat = await session.get(GroupChat, group_chat_id)
    if not group_chat:
        raise HTTPException(status_code=404, detail="Group chat not found")

    # Проверяем, что чат принадлежит текущему пользователю
    if group_chat.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Получаем агентов в чате через таблицу связей
    agent_rows = await session.execute(
        select(group_chat_agents.c.agent_id).where(
            group_chat_agents.c.group_chat_id == group_chat.id
        )
    )
    agent_ids = [str(row[0]) for row in agent_rows.fetchall()]

    if not agent_ids:
        raise HTTPException(status_code=400, detail="Group chat has no agents")

    # Загружаем объекты агентов
    result_agents = await session.execute(select(Agent).where(Agent.id.in_(agent_ids)))
    agents = result_agents.scalars().all()

    events: List[Event] = []

    for agent in agents:
        event = Event(
            description=payload.message,
            actor_id=agent.id,
            type="message",
            metadata_json=json.dumps({"group_chat_id": str(group_chat.id)}),
        )
        session.add(event)
        await session.flush()

        memory = Memory(
            agent_id=agent.id, description=payload.message, emotion=payload.emotion
        )
        session.add(memory)

        events.append(event)

        # Сохраняем в ChromaDB для быстрого поиска
        await memory_store.add_memory(agent.id, payload.message, payload.emotion)

    await session.commit()

    # Обновляем события после коммита и отправляем в WebSocket
    serialized_events: List[EventSchema] = []
    for event in events:
        await session.refresh(event)
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
        serialized_events.append(_serialize_event(event))

    logger.info(
        "Отправлено групповое сообщение в чат chat_id=%s для user_id=%s, создано событий=%d",
        group_chat_id,
        current_user.id,
        len(events),
    )
    return serialized_events
