# ---------------------------------------------------------
# Роутер для управления отношениями между агентами
# ---------------------------------------------------------

import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgr.db import get_session
from backend.database.postgr.models import Agent, Relationship, User
from backend.schemas import RelationSchema
from backend.services.deps import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/relations", tags=["relations"])


@router.get("", response_model=List[RelationSchema])
async def list_relations(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> List[RelationSchema]:
    """
    Получить все текущие отношения между агентами текущего пользователя.
    Проверяет оба агента (source и target), чтобы показать все отношения.
    """
    # Получаем ID всех агентов пользователя
    user_agents_result = await session.execute(
        select(Agent.id).where(Agent.user_id == current_user.id)
    )
    user_agent_ids = {str(agent_id[0]) for agent_id in user_agents_result.fetchall()}

    if not user_agent_ids:
        return []

    # Получаем отношения, где хотя бы один из агентов принадлежит пользователю
    result = await session.execute(
        select(Relationship).where(
            (Relationship.source_agent_id.in_(user_agent_ids)) |
            (Relationship.target_agent_id.in_(user_agent_ids))
        )
    )
    relations = result.scalars().all()

    # Фильтруем, чтобы показывать только отношения между агентами пользователя
    filtered_relations = [
        r for r in relations
        if str(r.source_agent_id) in user_agent_ids and str(r.target_agent_id) in user_agent_ids
    ]

    logger.info(
        "Запрос отношений для user_id=%s, найдено=%d",
        current_user.id,
        len(filtered_relations)
    )

    return [
        RelationSchema(
            source=str(r.source_agent_id),
            target=str(r.target_agent_id),
            affinity=r.affinity,
            label=r.label,
            strength=r.strength,
            updated_at=r.updated_at,
        )
        for r in filtered_relations
    ]
