# ---------------------------------------------------------
# Роутер для управления агентами
# ---------------------------------------------------------

import logging
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.chrome.db import memory_store
from backend.database.postgr.db import get_session
from backend.database.postgr.models import Agent, Event, Memory, Plan, Interaction, GroupChat, Relationship
from backend.database.postgr.models.groupchat import group_chat_agents
from backend.database.postgr.models import User
from backend.schemas import (
    AgentCreate,
    AgentSchema,
    EventSchema,
    InteractionSchema,
    MemorySchema,
    MessagePayload,
    PlanSchema,
)
from backend.services.deps import get_current_active_user
from backend.services.realtime import broker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def _build_agent_payload(
        session: AsyncSession, agent: Agent, detailed: bool = False
) -> AgentSchema:
    """
    Генерирует ответ по агенту — включает связанные планы, взаимодействия и последние воспоминания,
    если detailed=True (отдельный агент).
    """
    plans: List[Plan] = []
    interactions: List[Interaction] = []
    memories: List[MemorySchema] = []
    serialized_plans: List[PlanSchema] = []

    if detailed:
        # Загружаем последние 20 планов, отсортированные по дате создания (новые первыми)
        plan_rows = await session.execute(
            select(Plan)
            .where(Plan.agent_id == agent.id)
            .order_by(Plan.created_at.desc())
            .limit(20)
        )
        plans = plan_rows.scalars().all()
        logger.info(f"Загружено планов для агента {agent.id}: {len(plans)}")

        # Загружаем последние 20 взаимодействий, отсортированные по дате (новые первыми)
        inter_rows = await session.execute(
            select(Interaction)
            .where(Interaction.agent_id == agent.id)
            .order_by(Interaction.timestamp.desc())
            .limit(20)
        )
        interactions = inter_rows.scalars().all()

        # Загружаем последние 20 воспоминаний
        memory_items = await memory_store.fetch_agent_memories(agent.id, limit=20)
        memories = [
            MemorySchema(
                id=m.id,
                description=m.description,
                emotion=m.emotion,
                timestamp=m.timestamp,
            )
            for m in memory_items
        ]

    # Сериализуем планы
    if plans:
        for p in plans:
            try:
                serialized_plan = PlanSchema.model_validate(p)
                serialized_plans.append(serialized_plan)
            except Exception as e:
                logger.error(f"Ошибка при сериализации плана {p.id}: {e}")

    logger.info(f"Сериализовано планов для агента {agent.id}: {len(serialized_plans)}")

    return AgentSchema(
        id=agent.id,
        name=agent.name,
        mood=agent.mood,
        energy=agent.energy,
        traits=agent.traits or [],
        persona=agent.persona or {},
        current_task=agent.current_task,
        memories=memories,
        plans=serialized_plans,
        interactions=(
            [InteractionSchema.model_validate(i) for i in interactions]
            if interactions
            else []
        ),
    )


@router.get("", response_model=List[AgentSchema])
async def list_agents(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[AgentSchema]:
    """
    Вернуть список всех агентов текущего пользователя (коротко, без деталей).
    """
    # Фильтруем агентов по текущему пользователю
    result = await session.execute(
        select(Agent).where(Agent.user_id == current_user.id).order_by(Agent.created_at)
    )
    agents = result.scalars().all()
    logger.info("Запрос списка агентов для user_id=%s, количество=%d", current_user.id, len(agents))
    return [
        AgentSchema(
            id=a.id,
            name=a.name,
            mood=a.mood,
            energy=a.energy,
            traits=a.traits or [],
            persona=a.persona or {},
            current_task=a.current_task,
            memories=[],
            plans=[],
            interactions=[],
        )
        for a in agents
    ]


@router.get("/{agent_id}", response_model=AgentSchema)
async def get_agent(
        agent_id: str,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> AgentSchema:
    """
    Получить полный профиль агента (планы, воспоминания, взаимодействия).
    """
    # Проверяем принадлежность агента пользователю
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    logger.info("Запрос детальной информации агента id=%s для user_id=%s", agent.id, current_user.id)
    return await _build_agent_payload(session, agent, detailed=True)


@router.post("", response_model=AgentSchema, status_code=201)
async def create_agent(
        payload: AgentCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> AgentSchema:
    """
    Создать нового агента (имя, настроение, энергия и др.).
    Возвращает объект нового агента.
    """
    agent = Agent(
        name=payload.name,
        mood=payload.mood,
        energy=payload.energy,
        traits=payload.traits,
        persona=payload.persona,
        current_task=payload.current_task,
        user_id=current_user.id  # Привязываем агента к пользователю
    )
    session.add(agent)
    await session.flush()  # Получаем ID агента
    logger.info("Создание агента id=%s name=%s для user_id=%s", agent.id, agent.name, current_user.id)

    # Добавляем агента в дефолтный групповой чат "Кибер город"
    # Сначала находим дефолтный чат пользователя
    result = await session.execute(
        select(GroupChat).where(
            GroupChat.created_by_user_id == current_user.id,
            GroupChat.name == "Кибер город"
        )
    )
    default_chat = result.scalar_one_or_none()

    if default_chat:
        # Добавляем агента в дефолтный чат через таблицу связей,
        # чтобы не триггерить ленивую загрузку relationship в async-контексте
        await session.execute(
            insert(group_chat_agents).values(
                group_chat_id=default_chat.id,
                agent_id=agent.id,
            )
        )

    await session.commit()
    await session.refresh(agent)
    logger.info("Агент создан id=%s name=%s user_id=%s", agent.id, agent.name, current_user.id)
    return await _build_agent_payload(session, agent, detailed=False)


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


@router.post("/{agent_id}/message", response_model=EventSchema)
async def send_message_to_agent(
        agent_id: str,
        payload: MessagePayload,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> EventSchema:
    """
    Отправить агенту сообщение (создает Event + Memory).
    Также уведомляет через WebSocket/реалтайм.
    """
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Проверяем принадлежность агента пользователю
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    event = Event(description=payload.message, actor_id=agent.id, type="message")
    session.add(event)
    await session.flush()

    memory = Memory(
        agent_id=agent.id, description=payload.message, emotion=payload.emotion
    )
    session.add(memory)
    await session.commit()
    await session.refresh(event)
    logger.info("Отправлено сообщение агенту id=%s от user_id=%s, event_id=%s", agent.id, current_user.id, event.id)

    # Сохраняем в ChromaDB для быстрого поиска
    await memory_store.add_memory(agent.id, payload.message, payload.emotion)

    # Уведомляем по WebSocket
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


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
        agent_id: str,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
):
    """
    Удалить агента и все связанные с ним данные.
    Удаляет: события, воспоминания, планы, взаимодействия, отношения, связи с групповыми чатами.
    """
    # Проверяем принадлежность агента пользователю
    agent = await session.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    logger.info("Начало удаления агента id=%s name=%s для user_id=%s", agent.id, agent.name, current_user.id)

    # Удаляем воспоминания из ChromaDB
    try:
        await memory_store.delete_agent_memories(agent.id)
    except Exception as exc:
        logger.warning("Ошибка при удалении воспоминаний из ChromaDB: %s", exc)

    # Удаляем связи агента с групповыми чатами
    await session.execute(
        delete(group_chat_agents).where(group_chat_agents.c.agent_id == uuid.UUID(agent.id))
    )

    # Удаляем связанные данные (CASCADE должно обработать Relationships автоматически)
    # Но удаляем явно для ясности:
    await session.execute(
        delete(Event).where(Event.actor_id == agent.id)
    )
    await session.execute(
        delete(Event).where(Event.target_id == agent.id)
    )
    await session.execute(
        delete(Memory).where(Memory.agent_id == agent.id)
    )
    await session.execute(
        delete(Plan).where(Plan.agent_id == agent.id)
    )
    await session.execute(
        delete(Interaction).where(Interaction.agent_id == agent.id)
    )
    # Relationships удалятся автоматически через CASCADE, но можно удалить явно
    await session.execute(
        delete(Relationship).where(
            (Relationship.source_agent_id == agent.id) | (Relationship.target_agent_id == agent.id)
        )
    )

    # Удаляем самого агента
    await session.delete(agent)
    await session.commit()

    logger.info("Агент удален id=%s name=%s user_id=%s", agent.id, agent.name, current_user.id)

    # Уведомляем по WebSocket
    await broker.broadcast(
        {
            "type": "agent_deleted",
            "data": {
                "agent_id": agent_id,
            },
        }
    )
