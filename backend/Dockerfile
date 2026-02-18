# ----------------------------------------------------
#  Backend (FastAPI) Docker image
# ----------------------------------------------------
FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY backend/requirements.txt ./

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь код backend
COPY backend/ ./backend/

# Копируем alembic конфигурацию
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Открываем порт
EXPOSE 8000

# Устанавливаем рабочую директорию для backend
WORKDIR /app/backend

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
