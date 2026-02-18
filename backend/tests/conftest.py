from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def _test_env(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """
    Важно: settings/engine создаются при импорте backend.*.
    Поэтому env выставляем ДО импорта приложения.
    """
    # БД берём из env. Приоритет:
    # - SQLALCHEMY_TEST_URL (отдельная тестовая БД)
    # - SQLALCHEMY_URL (обычная)
    db_url = os.getenv("SQLALCHEMY_TEST_URL") or os.getenv("SQLALCHEMY_URL")
    if not db_url:
        # Фолбек, если env не задан: временная SQLite (удобно для запуска "из коробки")
        tmp_dir = tmp_path_factory.mktemp("backend-test")
        db_path = Path(tmp_dir) / "test.sqlite3"
        db_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
        os.environ["SQLALCHEMY_URL"] = db_url
    else:
        # В тестах всегда приводим к SQLALCHEMY_URL, т.к. код приложения читает именно её.
        os.environ["SQLALCHEMY_URL"] = db_url

    # Остальные настройки задаём только если пользователь не задал их сам
    os.environ.setdefault("BACKEND_TESTING", "1")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    os.environ.setdefault("OPENAI_API_KEY", "")
    os.environ.setdefault("CHROMA_API_KEY", "")
    os.environ.setdefault("CHROMA_TENANT", "")
    os.environ.setdefault("CHROMA_DB_NAME", "")

    return {
        "SQLALCHEMY_URL": os.environ["SQLALCHEMY_URL"],
        "BACKEND_TESTING": os.environ["BACKEND_TESTING"],
        "SECRET_KEY": os.environ["SECRET_KEY"],
    }


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_db(_test_env: dict[str, str]) -> AsyncIterator[None]:
    """
    Создаем таблицы один раз на всю сессию тестов.
    autouse=True гарантирует, что фикстура выполнится автоматически.
    Это должно быть сделано ДО импорта приложения, чтобы startup не падал.
    """
    # Важно: перед create_all() должны быть импортированы модели,
    # иначе Base.metadata будет пустой и таблицы не создадутся.
    from backend.database.postgr import models as _models  # noqa: F401
    from backend.database.postgr.db import Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Очистка после всех тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def _reset_db(_init_db: None) -> AsyncIterator[None]:
    """
    Очищаем данные между тестами, но таблицы уже созданы.
    """
    from backend.database.postgr import models as _models  # noqa: F401
    from backend.database.postgr.db import Base, engine
    from sqlalchemy import text

    # Удаляем все данные из таблиц, но сохраняем структуру.
    # Используем порядок Base.metadata.sorted_tables (он учитывает FK).
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        await conn.execute(text("PRAGMA foreign_keys=ON"))
    yield


@pytest_asyncio.fixture()
async def client(_init_db: None, _reset_db: None) -> AsyncIterator[httpx.AsyncClient]:
    """
    Создаем клиент для тестов. 
    _init_db гарантирует, что таблицы созданы до импорта приложения.
    _reset_db очищает данные перед каждым тестом.
    """
    from backend.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture()
async def auth_headers(client: httpx.AsyncClient) -> dict[str, str]:
    username = "user1"
    email = "user1@example.com"
    password = "pass12345"

    r = await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert r.status_code == 201, r.text

    r = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
