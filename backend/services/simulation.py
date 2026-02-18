from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database.chrome.db import memory_store
from backend.database.postgr.models import Agent, Event, GroupChat, Interaction, Memory, Plan, Relationship
from backend.database.postgr.models.groupchat import group_chat_agents

from backend.project_config import settings
from backend.schemas import SimulationStatus
from backend.services.llm import llm_client
from backend.services.realtime import broker

logger = logging.getLogger(__name__)


def _canon_uuid_str(value: str) -> Optional[str]:
    """
    Нормализует строку UUID в каноничную форму.
    Возвращает None, если это не UUID.
    """
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


class SimulationEngine:
    """
    Простой симулятор событий и настроений агентов.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self.is_paused = False
        self.speed = settings.SIMULATION_DEFAULT_SPEED
        self.tick_seconds = settings.SIMULATION_TICK_SECONDS
        self._task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="simulation-loop")
            logger.info("Цикл симуляции запущен")

    async def stop(self) -> None:
        self._shutdown = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("Цикл симуляции остановлен")

    async def control(self, action: Optional[str], speed: Optional[float]) -> SimulationStatus:
        if action == "pause":
            self.is_paused = True
            logger.info("Симуляция поставлена на паузу")
        elif action == "resume":
            self.is_paused = False
            logger.info("Симуляция возобновлена")

        if speed is not None:
            self.speed = max(0.1, min(speed, 10.0))
            logger.info("Скорость симуляции установлена на %.2fx", self.speed)

        return SimulationStatus(
            speed=self.speed, is_paused=self.is_paused, tick_seconds=self.tick_seconds
        )

    async def _get_group_chat_topics(self, session: AsyncSession, agent1: Agent, agent2: Agent) -> List[str]:
        """
        Получить список тем из групповых чатов, в которых участвуют оба агента.
        """
        # `Agent.id` хранится как String(64) (uuid-строка).
        # Нормализуем формат UUID и работаем со строками, т.к. group_chat_agents.c.agent_id тоже String.
        agent1_id = _canon_uuid_str(agent1.id)
        agent2_id = _canon_uuid_str(agent2.id)
        if not agent1_id or not agent2_id:
            return ["общение в кибер-городе"]

        # Получаем множества ID чатов для каждого агента через таблицу связей
        result1 = await session.execute(
            select(group_chat_agents.c.group_chat_id).where(
                group_chat_agents.c.agent_id == agent1_id
            )
        )
        chats1 = {row[0] for row in result1.fetchall()}

        result2 = await session.execute(
            select(group_chat_agents.c.group_chat_id).where(
                group_chat_agents.c.agent_id == agent2_id
            )
        )
        chats2 = {row[0] for row in result2.fetchall()}

        common_chat_ids = list(chats1 & chats2)
        if not common_chat_ids:
            return ["общение в кибер-городе"]

        result = await session.execute(
            select(GroupChat).where(GroupChat.id.in_(common_chat_ids))
        )
        group_chats = result.scalars().all()

        # Создаем контекст из названия и описания чата
        contexts = []
        for chat in group_chats:
            context = f"Чат: {chat.name}"
            if chat.description:
                context += f" - {chat.description}"
            contexts.append(context)

        return contexts if contexts else ["Чат: Кибер город - общение в кибер-городе"]

    async def _run(self) -> None:
        while not self._shutdown:
            if self.is_paused:
                await asyncio.sleep(0.25)
                continue

            try:
                await self.step()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - защитный лог
                logger.exception("Simulation step failed: %s", exc)

            await asyncio.sleep(max(0.2, self.tick_seconds / max(self.speed, 0.1)))

    async def step(self) -> None:
        async with self.session_factory() as session:
            agent = await self._pick_agent(session)
            if not agent:
                return

            # 60% вероятность общения (инициация или ответ), 40% - одиночное действие
            if random.random() < 0.6:
                # Сначала проверяем, есть ли недавние сообщения для ответа
                if random.random() < 0.4:
                    replied = await self._try_reply_to_message(session, agent)
                    if not replied:
                        # Если не удалось ответить, инициируем новое общение
                        await self._try_agent_chat(session, agent)
                else:
                    await self._try_agent_chat(session, agent)
            else:
                await self._try_agent_chat(session, agent)

            # С небольшой вероятностью создаем или обновляем планы агента
            if random.random() < 0.15:  # 15% вероятность создания плана
                await self._create_or_update_plan(session, agent)

    async def _try_agent_chat(self, session: AsyncSession, agent: Agent) -> None:
        """Попытка агента написать сообщение в общий групповой чат (не адресовано конкретному агенту)."""
        agent_id = _canon_uuid_str(agent.id)
        if not agent_id:
            return

        # Выбираем любой групповой чат, в котором состоит агент
        result_chats = await session.execute(
            select(group_chat_agents.c.group_chat_id).where(
                group_chat_agents.c.agent_id == agent_id
            )
        )
        chat_ids = [row[0] for row in result_chats.fetchall()]
        if not chat_ids:
            # Если агент не состоит ни в одном чате — просто возвращаемся
            logger.info(f"Агент {agent.name} не состоит ни в одном групповом чате")
            return

        # Берем один чат (можно расширить логикой выбора)
        group_chat_id = random.choice(chat_ids)

        # Проверяем, что в чате есть кроме него еще хотя бы один агент
        members_rows = await session.execute(
            select(group_chat_agents.c.agent_id).where(
                group_chat_agents.c.group_chat_id == group_chat_id
            )
        )
        member_ids = {str(row[0]) for row in members_rows.fetchall()}
        # Если в чате только этот агент – считаем, что общаться не с кем и ничего не делаем
        if member_ids <= {agent.id}:
            return
        chat_result = await session.execute(
            select(GroupChat).where(GroupChat.id == group_chat_id)
        )
        group_chat = chat_result.scalars().first()

        # Воспоминания и недавняя история (по желанию можно добавить фильтр по чату)
        memory_items = await memory_store.fetch_agent_memories(agent.id, limit=5)
        memories = [m.description for m in memory_items]

        # Генерируем сообщение через LLM на тему чата
        message_text: Optional[str] = None
        # Создаем полный контекст чата
        topic = f"Чат: {group_chat.name}"
        if group_chat.description:
            topic += f" - {group_chat.description}"
        else:
            topic += " - общение в чате"
        topic_source = "групповой чат"

        if llm_client.enabled:
            message_text = await llm_client.generate_message(
                sender_name=agent.name,
                sender_mood=agent.mood,
                sender_traits=agent.traits or [],
                receiver_name="участники чата",
                affinity=0.0,
                recent_memories=memories,
                conversation_history=[],
                sender_persona=agent.persona or "",
                receiver_traits=[],
                topic_hint=topic,
            )

        # Fallback если LLM не сработал
        if not message_text:
            message_text = f"Поделился мыслью в чате: {topic}"

        # Создаем групповое событие общения (без конкретного получателя)
        event_text = f"{agent.name} написал в чат «{group_chat.name}»: «{message_text}»"
        event = Event(
            description=event_text,
            actor_id=agent.id,
            target_id=None,
            type="chat_group",
            metadata_json=json.dumps(
                {
                    "topic": topic,
                    "topic_source": topic_source,
                    "group_chat_id": str(group_chat.id),
                }
            ),
        )

        # Обновляем настроение и энергию
        mood_delta = random.uniform(-0.05, 0.1)
        energy_delta = random.randint(-3, 2)
        agent.mood = max(0.0, min(1.0, agent.mood + mood_delta))
        agent.energy = max(0, min(100, agent.energy + energy_delta))
        agent.current_task = f"общается в чате «{group_chat.name}»"

        session.add(agent)
        session.add(event)

        # Создаем/обновляем отношения между отправителем и всеми участниками чата
        # Также создаем взаимодействия для всех участников и обновляем их настроение
        relationships_to_update = []
        interactions_to_create = []

        # Получаем объекты всех участников чата для обновления их настроения
        member_agents_result = await session.execute(
            select(Agent).where(Agent.id.in_([mid for mid in member_ids if mid != agent.id]))
        )
        member_agents = member_agents_result.scalars().all()

        for member_id in member_ids:
            if member_id != agent.id:
                try:
                    # Получаем объект участника
                    member_agent = next((a for a in member_agents if str(a.id) == member_id), None)
                    if not member_agent:
                        continue

                    # Создаем/обновляем отношения
                    relationship = await self._get_or_create_relationship(
                        session, agent.id, member_id
                    )

                    # Влияние сообщения на настроение и отношения зависит от контекста
                    # Положительные сообщения улучшают отношения, отрицательные - ухудшают
                    base_affinity_delta = random.uniform(0.01, 0.04)
                    # Если отношения уже положительные, они улучшаются быстрее
                    if relationship.affinity > 0:
                        affinity_delta = base_affinity_delta * 1.5
                    else:
                        affinity_delta = base_affinity_delta

                    relationship.affinity = max(-1.0, min(1.0, relationship.affinity + affinity_delta))
                    relationship.strength = min(1.0, relationship.strength + 0.01)
                    session.add(relationship)
                    relationships_to_update.append((member_id, relationship))

                    # Создаем взаимодействие для участника чата
                    interaction = Interaction(
                        agent_id=member_id,
                        partner=agent.name,
                        description=f"Услышал сообщение в чате «{group_chat.name}»: {message_text[:100]}",
                    )
                    session.add(interaction)
                    interactions_to_create.append(interaction)

                    # Обновляем настроение участника на основе отношения к отправителю
                    # Если отношения хорошие, настроение улучшается, если плохие - ухудшается
                    mood_influence = relationship.affinity * 0.02  # Влияние от -0.02 до +0.02
                    member_agent.mood = max(0.0, min(1.0, member_agent.mood + mood_influence))
                    member_agent.energy = max(0, min(100, member_agent.energy - 1))  # Небольшая трата энергии
                    session.add(member_agent)

                except Exception as e:
                    logger.warning(f"Ошибка при обновлении отношения с {member_id}: {e}")

        # Создаем взаимодействие для отправителя
        sender_interaction = Interaction(
            agent_id=agent.id,
            partner=f"участники чата «{group_chat.name}»",
            description=f"Написал в чат «{group_chat.name}»: {message_text[:100]}",
        )
        session.add(sender_interaction)

        # Улучшаем влияние сообщения на настроение отправителя на основе успешного общения
        # Если в чате много участников, настроение улучшается больше
        participants_bonus = len(member_ids) * 0.01
        mood_delta = random.uniform(-0.03, 0.08) + participants_bonus
        agent.mood = max(0.0, min(1.0, agent.mood + mood_delta))

        # Сохраняем в память с вероятностью
        memory_payload = None
        if random.random() < 0.5:  # Увеличиваем вероятность сохранения в память
            memory_payload = await memory_store.add_memory(
                agent_id=agent.id,
                description=f"Общался в чате «{group_chat.name}»: {message_text}",
                emotion=self._emotion_from_mood(agent.mood),
            )
            session.add(
                Memory(
                    agent_id=agent.id,
                    description=memory_payload.description,
                    emotion=memory_payload.emotion,
                    source_event_id=event.id,
                    timestamp=memory_payload.timestamp,
                )
            )

        await session.commit()
        await session.refresh(event)

        # Broadcast события
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
        await broker.broadcast(
            {
                "type": "agent_update",
                "data": {"id": agent.id, "mood": agent.mood, "energy": agent.energy},
            }
        )

        # Broadcast обновления отношений
        for member_id, relationship in relationships_to_update:
            await broker.broadcast(
                {
                    "type": "relation_changed",
                    "data": {
                        "source": agent.id,
                        "target": member_id,
                        "affinity": relationship.affinity,
                        "strength": relationship.strength,
                    },
                }
            )

        # Broadcast обновления настроения для всех участников чата
        for member_agent in member_agents:
            await broker.broadcast(
                {
                    "type": "agent_update",
                    "data": {"id": str(member_agent.id), "mood": member_agent.mood, "energy": member_agent.energy},
                }
            )

        if memory_payload:
            await broker.broadcast(
                {
                    "type": "memory_created",
                    "data": {"agent_id": agent.id, **memory_payload.as_response()},
                }
            )

    async def _pick_agent(self, session: AsyncSession) -> Optional[Agent]:
        result = await session.execute(select(Agent).order_by(func.random()).limit(1))
        return result.scalars().first()

    @staticmethod
    def _emotion_from_mood(mood: float) -> str:
        if mood >= 0.7:
            return "положительное"
        if mood >= 0.4:
            return "нейтральное"
        return "отрицательное"

    async def _pick_chat_target(self, session: AsyncSession, agent: Agent) -> Optional[Agent]:
        """Выбирает собеседника для агента на основе отношений и случайности."""
        # Сначала пытаемся общаться с агентами, с которыми есть общий групповой чат
        # Получаем ID чатов, в которых состоит агент
        agent_id = _canon_uuid_str(agent.id) or str(agent.id)
        result_chats = await session.execute(
            select(group_chat_agents.c.group_chat_id).where(
                group_chat_agents.c.agent_id == agent_id
            )
        )
        chat_ids = [row[0] for row in result_chats.fetchall()]

        chat_peers: List[Agent] = []
        if chat_ids:
            # Получаем ID агентов из этих чатов (кроме самого агента)
            result_peers = await session.execute(
                select(group_chat_agents.c.agent_id).where(
                    group_chat_agents.c.group_chat_id.in_(chat_ids)
                )
            )
            peer_ids = {str(row[0]) for row in result_peers.fetchall() if str(row[0]) != agent.id}

            if peer_ids:
                result_agents = await session.execute(
                    select(Agent).where(Agent.id.in_(list(peer_ids)))
                )
                chat_peers = result_agents.scalars().all()

        # Если есть собеседники по чату — используем только их, иначе все остальные
        if chat_peers:
            candidates = chat_peers
        else:
            result = await session.execute(
                select(Agent).where(Agent.id != agent.id)
            )
            candidates = result.scalars().all()

        if not candidates:
            return None

        # Получаем отношения
        rel_result = await session.execute(
            select(Relationship).where(Relationship.source_agent_id == agent.id)
        )
        relationships = {rel.target_agent_id: rel.affinity for rel in rel_result.scalars().all()}

        # Взвешенный выбор: предпочитаем агентов с положительными отношениями,
        # но иногда выбираем случайно для разнообразия
        if random.random() < 0.3:
            # 30% - случайный выбор среди кандидатов
            return random.choice(candidates)

        # 70% - выбор на основе отношений (предпочитаем друзей, но иногда и врагов)
        weighted_agents = []
        for other in candidates:
            affinity = relationships.get(other.id, 0.0)
            # Положительные отношения имеют больший вес, но отрицательные тоже возможны
            weight = max(0.1, affinity + 0.5) if affinity > 0 else max(0.05, abs(affinity) * 0.3)
            weighted_agents.append((weight, other))

        if weighted_agents:
            weights, agents = zip(*weighted_agents)
            return random.choices(agents, weights=weights, k=1)[0]

        # Если по каким-то причинам не удалось выбрать по весам — возвращаем случайного кандидата
        return random.choice(candidates) if candidates else None

    async def _get_or_create_relationship(
            self, session: AsyncSession, source_id: str, target_id: str
    ) -> Relationship:
        """Получает или создает отношение между агентами."""
        result = await session.execute(
            select(Relationship).where(
                Relationship.source_agent_id == source_id,
                Relationship.target_agent_id == target_id,
            )
        )
        rel = result.scalars().first()
        if not rel:
            rel = Relationship(
                source_agent_id=source_id,
                target_agent_id=target_id,
                affinity=0.0,
                strength=0.5,
            )
            session.add(rel)
        return rel

    async def _try_reply_to_message(self, session: AsyncSession, agent: Agent) -> bool:
        """Пытается ответить на недавнее сообщение от другого агента."""
        # Ищем недавние события-чаты, где этот агент был получателем
        recent_time = datetime.utcnow() - timedelta(minutes=5)

        result = await session.execute(
            select(Event)
            .where(
                Event.target_id == agent.id,
                Event.type == "chat",
                Event.created_at >= recent_time,
            )
            .order_by(Event.created_at.desc())
            .limit(1)
        )
        recent_event = result.scalars().first()

        if not recent_event or not recent_event.actor_id:
            return False

        # Получаем отправителя
        sender_result = await session.execute(
            select(Agent).where(Agent.id == recent_event.actor_id)
        )
        sender = sender_result.scalars().first()
        if not sender:
            return False

        # Получаем или создаем отношение
        relationship = await self._get_or_create_relationship(session, agent.id, sender.id)

        # Получаем историю общения
        recent_interactions = await self._get_recent_interactions(session, agent.id, sender.name)
        conversation_history = [
            {"from": i.partner or sender.name, "text": i.description}
            for i in recent_interactions[-5:]
        ]
        # Добавляем последнее сообщение от отправителя
        if recent_event.description:
            conversation_history.append({
                "from": sender.name,
                "text": recent_event.description.split(": «")[-1].rstrip(
                    "»") if "«" in recent_event.description else recent_event.description
            })

        # Получаем воспоминания
        memory_items = await memory_store.fetch_agent_memories(agent.id, limit=5)
        memories = [m.description for m in memory_items]

        # Генерируем ответ через LLM
        reply_text: Optional[str] = None
        if llm_client.enabled:
            reply_text = await llm_client.generate_message(
                sender_name=agent.name,
                sender_mood=agent.mood,
                sender_traits=agent.traits or [],
                receiver_name=sender.name,
                affinity=relationship.affinity,
                recent_memories=memories,
                conversation_history=conversation_history,
                sender_persona=agent.persona or "",
                receiver_traits=sender.traits or [],
            )

        # Fallback
        if not reply_text:
            if relationship.affinity > 0.3:
                reply_text = "Спасибо! У меня тоже всё хорошо."
            elif relationship.affinity < -0.3:
                reply_text = "Хм, интересно..."
            else:
                reply_text = "Понял."

        # Создаем событие ответа
        event_text = f"{agent.name} ответил {sender.name}: «{reply_text}»"
        event = Event(
            description=event_text,
            actor_id=agent.id,
            target_id=sender.id,
            type="chat",
        )

        # Сохраняем взаимодействие
        interaction = Interaction(
            agent_id=agent.id,
            partner=sender.name,
            description=reply_text,
        )

        # Обновляем настроение и энергию
        mood_delta = random.uniform(-0.05, 0.1) if relationship.affinity > 0 else random.uniform(-0.1, 0.05)
        energy_delta = random.randint(-3, 2)
        agent.mood = max(0.0, min(1.0, agent.mood + mood_delta))
        agent.energy = max(0, min(100, agent.energy + energy_delta))
        agent.current_task = f"отвечает {sender.name}"

        # Обновляем отношения
        affinity_delta = random.uniform(0.02, 0.08) if relationship.affinity >= 0 else random.uniform(-0.05, 0.02)
        relationship.affinity = max(-1.0, min(1.0, relationship.affinity + affinity_delta))
        relationship.strength = min(1.0, relationship.strength + 0.01)

        session.add(agent)
        session.add(event)
        session.add(interaction)
        session.add(relationship)

        # Сохраняем в память
        memory_payload = None
        if random.random() < 0.4:
            memory_payload = await memory_store.add_memory(
                agent_id=agent.id,
                description=f"Ответил {sender.name}: {reply_text}",
                emotion=self._emotion_from_mood(agent.mood),
            )
            session.add(
                Memory(
                    agent_id=agent.id,
                    description=memory_payload.description,
                    emotion=memory_payload.emotion,
                    source_event_id=event.id,
                    timestamp=memory_payload.timestamp,
                )
            )

        await session.commit()
        await session.refresh(event)

        # Broadcast
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
        await broker.broadcast(
            {
                "type": "agent_update",
                "data": {"id": agent.id, "mood": agent.mood, "energy": agent.energy},
            }
        )
        await broker.broadcast(
            {
                "type": "relation_changed",
                "data": {
                    "source": agent.id,
                    "target": sender.id,
                    "affinity": relationship.affinity,
                    "strength": relationship.strength,
                },
            }
        )

        if memory_payload:
            await broker.broadcast(
                {
                    "type": "memory_created",
                    "data": {"agent_id": agent.id, **memory_payload.as_response()},
                }
            )

        return True

    async def _get_recent_interactions(
            self, session: AsyncSession, agent_id: str, partner_name: str, limit: int = 5
    ) -> List[Interaction]:
        """Получает недавние взаимодействия между агентами."""
        result = await session.execute(
            select(Interaction)
            .where(
                (Interaction.agent_id == agent_id) & (Interaction.partner == partner_name)
            )
            .order_by(Interaction.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _build_action_text(self, session: AsyncSession, agent: Agent) -> str:
        """
        Пытаемся получить действие от LLM, иначе fallback на рандом.
        """
        llm_text: Optional[str] = None
        if llm_client.enabled:
            memory_items = await memory_store.fetch_agent_memories(agent.id, limit=5)
            memories = [m.description for m in memory_items]
            llm_text = await llm_client.generate_action(
                agent_name=agent.name,
                mood=agent.mood,
                energy=agent.energy,
                current_task=agent.current_task,
                memories=memories,
                traits=agent.traits or [],
                persona=agent.persona or "",
            )
        if llm_text:
            return f"{agent.name} {llm_text}"
        return f"{agent.name} {agent.current_task}"

    async def _create_or_update_plan(self, session: AsyncSession, agent: Agent) -> None:
        """
        Создает или обновляет план для агента на основе его текущего состояния и воспоминаний.
        """
        # Проверяем, есть ли у агента активные планы
        result = await session.execute(
            select(Plan).where(
                Plan.agent_id == agent.id,
                Plan.status.in_(["active", "planned", "in-progress"])
            ).limit(1)
        )
        existing_plan = result.scalars().first()

        # Если планов нет или с небольшой вероятностью создаем новый
        if not existing_plan or random.random() < 0.1:
            # Получаем контекст чата для более релевантных планов
            group_chat = await self._get_agent_chat(session, agent)
            chat_name = group_chat.name if group_chat else "город"

            # Генерируем план на основе текущего состояния агента
            plan_titles_positive = [
                "Изучить новые технологии",
                "Улучшить отношения с другими агентами",
                f"Исследовать {chat_name}",
                "Развить навыки общения",
                "Найти интересные места в городе",
                "Помочь другим агентам",
                "Изучить историю кибер-города",
            ]

            plan_titles_neutral = [
                "Изучить новые технологии",
                "Улучшить отношения с другими агентами",
                f"Исследовать {chat_name}",
                "Развить навыки общения",
                "Найти интересные места",
            ]

            plan_titles_negative = [
                "Улучшить настроение",
                "Найти поддержку",
                "Отдохнуть",
                "Разобраться в проблемах",
                "Восстановить энергию",
            ]

            plan_descriptions = [
                "Агент планирует изучить новые технологии и улучшить свои навыки",
                "Агент хочет улучшить отношения с другими участниками города",
                "Агент планирует исследовать различные места и найти что-то интересное",
                "Агент хочет развить свои навыки общения и взаимодействия",
                "Агент планирует помочь другим агентам в их делах",
            ]

            # Выбираем план на основе настроения и энергии
            if agent.mood > 0.7:
                plan_title = random.choice(plan_titles_positive)
            elif agent.mood < 0.4:
                plan_title = random.choice(plan_titles_negative)
            else:
                plan_title = random.choice(plan_titles_neutral)

            plan_description = random.choice(plan_descriptions)

            plan = Plan(
                agent_id=agent.id,
                title=plan_title,
                description=plan_description,
                status="active" if random.random() < 0.7 else "planned",
            )
            session.add(plan)
            await session.commit()
            await session.refresh(plan)
            logger.info(f"Создан план для агента {agent.name}: {plan_title} (id: {plan.id})")

    async def _get_agent_chat(self, session: AsyncSession, agent: Agent) -> Optional[GroupChat]:
        """Получает первый групповой чат агента для контекста."""
        agent_id = _canon_uuid_str(agent.id)
        if not agent_id:
            return None
        result_chats = await session.execute(
            select(group_chat_agents.c.group_chat_id).where(
                group_chat_agents.c.agent_id == agent_id
            ).limit(1)
        )
        chat_ids = [row[0] for row in result_chats.fetchall()]
        if chat_ids:
            chat_result = await session.execute(
                select(GroupChat).where(GroupChat.id == chat_ids[0])
            )
            return chat_result.scalars().first()
        return None
