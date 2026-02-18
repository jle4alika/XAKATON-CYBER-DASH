from __future__ import annotations

"""
Утилиты инициализации схемы и стартовых данных.

Сейчас init_schema отвечает только за создание таблиц на основе metadata,
а ensure_seed_data оставлена как "hook" для возможного будущего наполнения БД.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database.postgr.db import Base, engine

logger = logging.getLogger(__name__)


async def init_schema() -> None:
    """
    Создать отсутствующие таблицы на основе Base.metadata.

    Используется при старте приложения, если миграции ещё не настроены
    или требуется быстро поднять чистую БД для разработки.
    """
    logger.info("Инициализация схемы БД через Base.metadata.create_all")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Инициализация схемы БД завершена")


async def ensure_seed_data(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Хук для наполнения БД начальными данными.

    По текущим требованиям БД должна быть пустой при старте,
    поэтому функция ничего не делает, но оставлена для расширения.
    """
    logger.debug("ensure_seed_data вызвана — логика наполнения начальными данными не настроена")
    return
