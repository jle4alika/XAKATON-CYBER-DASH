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
    Получить все текущие отношения между агентами.
    """
    # Получаем отношения только для агентов текущего пользователя
    result = await session.execute(
        select(Relationship)
        .join(Agent, Relationship.source_agent_id == Agent.id)
        .where(Agent.user_id == current_user.id)
    )
    relations = result.scalars().all()
    return [
        RelationSchema(
            source=r.source_agent_id,
            target=r.target_agent_id,
            affinity=r.affinity,
            label=r.label,
            strength=r.strength,
            updated_at=r.updated_at,
        )
        for r in relations
    ]
