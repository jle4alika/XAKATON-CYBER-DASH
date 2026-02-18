from __future__ import annotations

import asyncio
import logging
from logging.config import fileConfig
from typing import Any, Dict

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Эта переменная заполняется из alembic.ini (sqlalchemy.url),
# но мы переопределим её через settings.SQLALCHEMY_URL.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")


def get_settings_url() -> str:
    """
    Берём URL БД из backend.project_config.Settings,
    чтобы alembic использовал тот же DSN, что и приложение.
    """
    from backend.project_config import settings

    return settings.SQLALCHEMY_URL


# Импортируем Base и все модели, чтобы alembic знал целевую метадату.
from backend.database.postgr.db import Base  # noqa: E402
from backend.database.postgr import models  # noqa: F401,E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме."""
    url = get_settings_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Основной async-путь для online-миграций."""
    connectable: AsyncEngine = create_async_engine(
        get_settings_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск миграций в online-режиме (через AsyncEngine)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
