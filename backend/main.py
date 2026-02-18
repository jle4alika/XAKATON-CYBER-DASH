# ---------------------------------------------------------
# Основной файл backend FastAPI для проекта симуляции агентов
# Инициализация приложения, middleware, обработчики ошибок и события жизненного цикла
# ---------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.database.postgr.db import async_session
from backend.project_config import settings
from backend.services.seed import ensure_seed_data, init_schema
from backend.services.simulation import SimulationEngine

# Импорт роутеров
from backend.routers import auth, users, agents, group_chats, events, relations, simulation, websocket


# Настройка логирования в файл
def setup_logging():
    """
    Настройка логирования в файл с именем, содержащим дату и время запуска.
    Логи сохраняются в папке logs/ в корне проекта.
    """
    # Создаем папку logs если её нет
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Формируем имя файла с датой и временем запуска
    start_time = datetime.now()
    log_filename = start_time.strftime("%Y-%m-%d_%H-%M-%S.log")
    log_filepath = logs_dir / log_filename

    # Настраиваем формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Настраиваем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Очищаем существующие обработчики
    root_logger.handlers.clear()

    # Обработчик для записи в файл
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)

    # Добавляем обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Логируем информацию о запуске
    logger = logging.getLogger(__name__)
    logger.info(f"Логирование настроено. Файл лога: {log_filepath}")

    return log_filepath


# Настраиваем логирование при импорте модуля
log_filepath = setup_logging()
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения, движка симуляции и сервисов
app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)
sim_engine = SimulationEngine(async_session)

# Настройка CORS для фронтенда (можно потом ограничить)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Обработчик ошибок JWT
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 401:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": "Unauthorized"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Подключение роутеров
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(agents.router)
app.include_router(group_chats.router)
app.include_router(events.router)
app.include_router(relations.router)
# Устанавливаем экземпляр движка симуляции в роутер
simulation.set_sim_engine(sim_engine)
app.include_router(simulation.router)
app.include_router(websocket.router)


# ----- События жизненного цикла приложения -----


@app.on_event("startup")
async def on_startup() -> None:
    """
    Действия при запуске приложения:
    - Инициализация схемы таблиц
    - Начальное наполнение базы (seed)
    - Старт симуляции (tick loop)
    """
    logger.info("=" * 80)
    logger.info(f"Запуск приложения {settings.API_TITLE} версии {settings.API_VERSION}")
    logger.info(f"Логи сохраняются в файл: {log_filepath}")
    logger.info("=" * 80)
    await init_schema()
    await ensure_seed_data(async_session)
    await sim_engine.start()
    logger.info("API started")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """
    Корректная остановка симуляции при завершении работы.
    """
    await sim_engine.stop()
