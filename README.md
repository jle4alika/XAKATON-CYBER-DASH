# КИБЕР РЫВОК — симулятор живого кибер‑города

Современный playground, где живут AI‑агенты с характерами, памятью и отношениями.  
Вы создаёте персонажей, объединяете их в групповые чаты и наблюдаете за тем, как они **общаются, запоминают события и
меняют отношение друг к другу** в реальном времени.

---

## Архитектура

### Backend — FastAPI + PostgreSQL + ChromaDB

- **FastAPI**: REST API + WebSocket‑стрим событий (`/ws/events`).
- **PostgreSQL**: хранение пользователей, агентов, событий, отношений и групповых чатов.
- **ChromaDB**: векторное хранилище воспоминаний агентов для более реалистичного контекста.
- **LLM‑слой**: `backend/services/llm.py` — генерация действий и сообщений агентов на основе:
    - настроения и энергии,
    - черт характера,
    - текстового описания персонажа,
    - истории общения и воспоминаний,
    - названия и описания чата.
- **Аутентификация и авторизация**:
    - регистрация пользователей (`POST /api/auth/register`),
    - вход в систему (`POST /api/auth/login`),
    - JWT‑токены для защиты API,
    - каждый пользователь видит только своих агентов и чаты,
    - все эндпоинты (кроме регистрации и входа) требуют JWT токен.
- **API Роутеры** (модульная структура):
    - `/api/auth` — аутентификация (register, login),
    - `/api/users` — управление пользователями (me),
    - `/api/agents` — управление агентами (CRUD, отправка сообщений),
    - `/api/group-chats` — групповые чаты (создание, управление, сообщения),
    - `/api/events` — события симуляции,
    - `/api/relations` — отношения между агентами,
    - `/api/simulation` — управление симуляцией (пауза, скорость),
    - `/ws/events` — WebSocket для событий в реальном времени.
- **Симуляция**:
    - `SimulationEngine` крутится в фоне,
    - агенты генерируют события/сообщения,
    - изменения транслируются по WebSocket во фронтенд.

### Frontend — React + Vite + Zustand

- **Страницы приложения**:
    - **MainPage** (`/`) — лендинг с описанием проекта,
    - **LoginPage** (`/login`) — страница входа,
    - **RegisterPage** (`/register`) — страница регистрации,
    - **DashboardPage** (`/dashboard`) — главный дашборд со списком агентов, их настроением/энергией, панель управления
      временем,
    - **AgentPage** (`/agent/:id`) — детальный профиль агента: память, планы, история взаимодействий, чат с агентом,
    - **GroupChatPage** (`/group-chat`) — групповые чаты, где несколько агентов обсуждают ситуацию из описания чата,
    - **RelationsPage** (`/relations`) — визуализация графа отношений (симпатии/антипатии между агентами),
    - **SettingsPage** (`/settings`) — настройки приложения,
    - **NotFoundPage** (`*`) — страница 404.
- **Защита маршрутов**: `AuthWrapper` компонент проверяет наличие JWT токена для приватных страниц.
- **Состояние и запросы**:
    - Zustand‑сторы (`agentStore`, `eventStore`, `simulationStore`, `errorStore`),
        - слой `services/api.js` и `services/websocket.js` для HTTP+WS‑коммуникации.
- **Организация стилей**:
    - CSS модули для каждой страницы и компонента,
    - глобальные стили разделены на `variables.css`, `global.css`, `utilities.css`.

---

## Быстрый старт

### 1. Backend

Перейдите в директорию `backend` и установите зависимости:

```bash
cd backend
pip install -r requirements.txt
```

Создайте файл `.env` в директории `backend/`:

```env
# ============================================
# PostgreSQL Database
# ============================================
# Формат: postgresql+asyncpg://user:password@host:port/database
SQLALCHEMY_URL=postgresql+asyncpg://cyber_user:cyber_password@localhost:5432/cyber_city

# ============================================
# JWT Authentication
# ============================================
# Секретный ключ для подписи JWT токенов (сгенерируйте случайную строку)
# Можно использовать: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-secret-key-change-this-to-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# OpenAI / LLM Configuration
# ============================================
# API ключ OpenAI (или совместимого сервиса)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# ============================================
# ChromaDB Configuration
# ============================================
# Вариант 1: Локальное хранилище (по умолчанию)
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION=memories

# Вариант 2: ChromaDB Cloud (раскомментируйте и заполните)
# CHROMA_API_KEY=your-chroma-cloud-api-key
# CHROMA_TENANT=your-chroma-tenant
# CHROMA_DB_NAME=your-chroma-database-name

# Вариант 3: Удаленный ChromaDB сервер (раскомментируйте при необходимости)
# CHROMA_HOST=localhost
# CHROMA_PORT=8000
# CHROMA_SSL=false

# ============================================
# Simulation Settings
# ============================================
# Интервал между тиками симуляции (в секундах)
SIMULATION_TICK_SECONDS=1.0
# Скорость симуляции по умолчанию
SIMULATION_DEFAULT_SPEED=1.0

# ============================================
# API Settings
# ============================================
API_TITLE=КИБЕР РЫВОК API
API_VERSION=0.1.0
```

**Важно:**

- Замените `SECRET_KEY` на случайную строку (можно сгенерировать командой:
  `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Укажите свой `OPENAI_API_KEY` для работы LLM
- Настройте `SQLALCHEMY_URL` в соответствии с вашей PostgreSQL базой данных
- Для локального запуска можно использовать значения по умолчанию для ChromaDB

**Для Docker (дополнительно):**

Если планируете использовать Docker, добавьте в `backend/.env` переменные для PostgreSQL контейнера:

```env
# Переменные для PostgreSQL контейнера (используются в docker-compose.yml)
POSTGRES_USER=cyber_user
POSTGRES_PASSWORD=cyber_password
POSTGRES_DB=cyber_city
```

Эти переменные используются для автоматической настройки PostgreSQL контейнера.

**Миграции (Async Alembic)**

```bash
# из корня проекта, с активированным backend/venv
backend\venv\Scripts\alembic.exe revision --autogenerate -m "init"
backend\venv\Scripts\alembic.exe upgrade head
```

Запуск сервера разработки:

```bash
uvicorn backend.main:app --reload
```

Backend будет доступен по адресу `http://localhost:8000`, OpenAPI — на `/docs`.

### 2. Frontend

Перейдите в директорию `frontend` и установите зависимости:

```bash
cd frontend
npm install
```

При необходимости создайте `frontend/.env` (или `.env.local`) с базовым URL API и WS:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

Запуск dev‑сервера:

```bash
npm run dev
```

По умолчанию фронтенд поднимется на `http://localhost:5173` (или другом свободном порту Vite).

---

## Запуск через Docker (рекомендуется)

### Предварительные требования

- Docker и Docker Compose установлены на вашем ПК
- Файл `backend/.env` создан и настроен (см. раздел выше)

### Быстрый старт с Docker

1. **Создайте файл `backend/.env`** с настройками (см. полный пример выше)

2. **Запустите все сервисы:**

```bash
docker-compose up -d
```

Это запустит:

- PostgreSQL базу данных (порт 5432)
- Backend FastAPI сервер (порт 8000)
- Frontend React приложение (порт 3000)

3. **Проверьте статус сервисов:**

```bash
docker-compose ps
```

4. **Просмотрите логи:**

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

5. **Выполните миграции базы данных:**

```bash
# Войдите в контейнер backend
docker-compose exec backend bash

# Выполните миграции
alembic upgrade head
```

6. **Остановите сервисы:**

```bash
docker-compose down
```

### Переменные окружения для Docker

В `docker-compose.yml` используются переменные из `backend/.env`. Убедитесь, что в `.env` указаны:

```env
POSTGRES_USER=cyber_user
POSTGRES_PASSWORD=cyber_password
POSTGRES_DB=cyber_city
```

Эти переменные используются для настройки PostgreSQL контейнера.

### Полезные команды Docker

```bash
# Пересобрать образы
docker-compose build

# Пересобрать и перезапустить
docker-compose up -d --build

# Остановить и удалить контейнеры (данные БД сохранятся)
docker-compose down

# Остановить и удалить всё, включая volumes (удалит данные БД!)
docker-compose down -v

# Просмотр логов конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

---

## Пользовательский флоу

### Регистрация и вход

1. **Регистрация**: Зарегистрируйтесь на странице `/register` или через API `POST /api/auth/register`:
   ```json
   {
     "username": "string",
     "email": "string",
     "password": "string"
   }
   ```

   **Требования к паролю:**

- Минимум 8 символов
- Хотя бы одна заглавная буква (латиница или кириллица)
- Хотя бы одна строчная буква (латиница или кириллица)
- Хотя бы одна цифра
- Хотя бы один специальный символ (!@#$%^&*()_+-=[]{};':"\\|,.<>/?)

На странице регистрации реализована валидация пароля в реальном времени:

- При вводе пароля отображается список требований с визуальными индикаторами (✓/✗)
- Форма не отправляется, если пароль не соответствует требованиям
- Проверяется совпадение пароля и подтверждения пароля

2. **Вход**: Войдите на странице `/login` или через API `POST /api/auth/login`:
   ```json
   {
     "username": "string",
     "password": "string"
   }
   ```
   Получите JWT токен, который автоматически сохраняется в `localStorage`.

3. **Доступ к приложению**: После логина доступны все защищенные страницы:

- `/dashboard` — дашборд агентов,
- `/group-chat` — групповые чаты,
- `/agent/:id` — профиль агента,
- `/relations` — граф отношений,
- `/settings` — настройки симуляции.

### Работа с агентами

- **Создание агентов**: Через UI на дашборде создавайте агентов с указанием:
    - имени,
    - настроения (mood),
    - энергии (energy),
    - черт характера (traits),
    - текстового описания персонажа (persona).
- **Просмотр агентов**: На дашборде видите список всех своих агентов с их текущим состоянием.
- **Детальный профиль**: Переходите на `/agent/:id` для просмотра:
    - памяти агента (воспоминания из векторной БД),
    - планов,
    - истории взаимодействий,
    - возможности отправки сообщений агенту.

### Групповые чаты

- **Создание чата**: Объединяйте агентов в групповые чаты с:
    - названием чата,
    - описанием ситуации/сцены — это и есть **контекст для общения агентов**.
- **Управление чатом**: Добавляйте/удаляйте агентов, отправляйте сообщения в чат.
- **Симуляция в чатах**: Симуляция заставляет агентов:
    - общаться в рамках ситуаций, заданных описанием чата,
    - запоминать важные события в векторную БД,
    - менять отношение друг к другу на основе взаимодействий.

### Граф отношений

- Визуализация всех отношений между вашими агентами.
- Цвет рёбер отражает уровень симпатии/антипатии.
- Граф обновляется в реальном времени по мере развития отношений.

---

## Структура проекта

```text
hakaton-16-02-2026/
├── backend/                      # Бэкенд на FastAPI
│   ├── database/
│   │   ├── postgr/              # Модели и async-движок PostgreSQL
│   │   │   ├── models/         # ORM модели (User, Agent, Event, GroupChat, etc.)
│   │   │   └── db.py            # Настройка async сессий
│   │   └── chrome/              # Интеграция с ChromaDB
│   │       └── db.py            # Векторное хранилище воспоминаний
│   ├── routers/                 # Роутеры FastAPI (разделены по функциональности)
│   │   ├── auth.py              # Аутентификация (register, login)
│   │   ├── users.py             # Управление пользователями (/api/users/me)
│   │   ├── agents.py            # Управление агентами
│   │   ├── group_chats.py       # Групповые чаты
│   │   ├── events.py            # События симуляции
│   │   ├── relations.py         # Отношения между агентами
│   │   ├── simulation.py        # Управление симуляцией
│   │   └── websocket.py         # WebSocket соединения
│   ├── services/                # Бизнес-логика
│   │   ├── auth.py              # Аутентификация и авторизация
│   │   ├── deps.py              # Зависимости (get_current_active_user)
│   │   ├── llm.py               # LLM-интеграция
│   │   ├── simulation.py        # Движок симуляции
│   │   ├── realtime.py          # WebSocket брокер
│   │   └── seed.py              # Начальные данные
│   ├── schemas.py               # Pydantic-схемы для API
│   ├── main.py                  # Инициализация FastAPI, middleware, подключение роутеров
│   ├── middleware.py            # Middleware для аутентификации
│   └── project_config.py        # Настройки и .env
├── alembic/                     # Конфигурация async Alembic для миграций
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                # Папка для автогенерируемых миграций
├── frontend/                    # Фронтенд на React/Vite
│   ├── src/
│   │   ├── components/          # Переиспользуемые UI-компоненты
│   │   │   ├── AddAgentForm/
│   │   │   ├── AgentCard/
│   │   │   ├── AgentGrid/
│   │   │   ├── AgentProfile/
│   │   │   ├── EventStream/
│   │   │   ├── GlobalActionPanel/
│   │   │   ├── MemoryList/
│   │   │   ├── MessageInput/
│   │   │   ├── Navbar/
│   │   │   ├── RelationGraph/
│   │   │   └── TimeControlPanel/
│   │   ├── pages/               # Страницы приложения (каждая в своей папке)
│   │   │   ├── MainPage/        # Главная страница (лендинг)
│   │   │   │   ├── MainPage.jsx
│   │   │   │   └── MainPage.module.css
│   │   │   ├── DashboardPage/   # Дашборд с агентами
│   │   │   │   ├── DashboardPage.jsx
│   │   │   │   └── DashboardPage.module.css
│   │   │   ├── LoginPage/       # Страница входа
│   │   │   │   ├── LoginPage.jsx
│   │   │   │   └── LoginPage.module.css
│   │   │   ├── RegisterPage/    # Страница регистрации
│   │   │   │   ├── RegisterPage.jsx
│   │   │   │   └── RegisterPage.module.css
│   │   │   ├── GroupChatPage/   # Групповые чаты
│   │   │   │   ├── GroupChatPage.jsx
│   │   │   │   └── GroupChatPage.module.css
│   │   │   ├── AgentPage/       # Профиль агента
│   │   │   │   ├── AgentPage.jsx
│   │   │   │   └── AgentPage.module.css
│   │   │   ├── RelationsPage/   # Граф отношений
│   │   │   │   ├── RelationsPage.jsx
│   │   │   │   └── RelationsPage.module.css
│   │   │   ├── SettingsPage/    # Настройки
│   │   │   │   ├── SettingsPage.jsx
│   │   │   │   └── SettingsPage.module.css
│   │   │   └── NotFoundPage/    # Страница 404
│   │   │       ├── NotFoundPage.jsx
│   │   │       └── NotFoundPage.module.css
│   │   ├── styles/              # Глобальные стили (разделены на модули)
│   │   │   ├── variables.css     # CSS переменные
│   │   │   ├── global.css       # Глобальные стили (body, html, базовые элементы)
│   │   │   └── utilities.css    # Утилитарные классы (переиспользуемые стили)
│   │   ├── services/            # HTTP/WS-клиенты
│   │   │   ├── api.js           # REST API клиент
│   │   │   ├── websocket.js     # WebSocket клиент
│   │   │   └── simulation.js    # Управление симуляцией
│   │   ├── store/               # Zustand‑сторы
│   │   │   ├── agentStore.js    # Состояние агентов
│   │   │   ├── eventStore.js    # Состояние событий
│   │   │   ├── simulationStore.js # Состояние симуляции
│   │   │   └── errorStore.js    # Состояние ошибок
│   │   ├── types/               # Типы данных для фронта (JSDoc)
│   │   ├── App.jsx              # Корневой компонент с роутингом
│   │   ├── main.jsx             # Точка входа
│   │   └── index.css            # Главный файл стилей (импортирует styles/*)
│   └── assets/                  # Статические ресурсы (изображения, иконки)
└── README.md                    # Этот файл
```

---

## API Документация

После запуска backend сервера, полная интерактивная документация API доступна по адресу:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Основные эндпоинты

#### Аутентификация (публичные)

- `POST /api/auth/register` — регистрация нового пользователя
- `POST /api/auth/login` — вход и получение JWT токена

#### Пользователи (защищенные)

- `GET /api/users/me` — информация о текущем пользователе

#### Агенты (защищенные)

- `GET /api/agents` — список всех агентов текущего пользователя
- `GET /api/agents/{agent_id}` — детальная информация об агенте
- `POST /api/agents` — создание нового агента
- `POST /api/agents/{agent_id}/message` — отправка сообщения агенту

#### Групповые чаты (защищенные)

- `GET /api/group-chats` — список всех групповых чатов
- `GET /api/group-chats/{chat_id}` — детальная информация о чате
- `POST /api/group-chats` — создание нового группового чата
- `PUT /api/group-chats/{chat_id}` — обновление чата
- `DELETE /api/group-chats/{chat_id}` — удаление чата
- `POST /api/group-chats/{chat_id}/message` — отправка сообщения в чат

#### События (защищенные)

- `GET /api/events` — список событий симуляции

#### Отношения (защищенные)

- `GET /api/relations` — список всех отношений между агентами

#### Симуляция (защищенные)

- `POST /api/simulation/control` — управление симуляцией (пауза, изменение скорости)

#### WebSocket

- `WS /ws/events` — поток событий в реальном времени

**Примечание**: Все эндпоинты, кроме `/api/auth/register` и `/api/auth/login`, требуют JWT токен в заголовке
`Authorization: Bearer <token>`.

## Развертывание на сервере (Production)

### Использование Nginx

Для production развертывания используйте шаблон конфигурации Nginx из `nginx/nginx.conf.template`:

1. **Скопируйте шаблон:**

```bash
cp nginx/nginx.conf.template /etc/nginx/sites-available/cyber-ryvok
```

2. **Отредактируйте конфигурацию:**

Замените `your-domain.com` на ваш домен и настройте SSL сертификаты (Let's Encrypt).

3. **Активируйте конфигурацию:**

```bash
ln -s /etc/nginx/sites-available/cyber-ryvok /etc/nginx/sites-enabled/
nginx -t  # Проверка конфигурации
systemctl reload nginx
```

4. **Обновите docker-compose.yml:**

В production рекомендуется:

- Убрать volume монтирование кода (использовать только собранные образы)
- Настроить правильные переменные окружения
- Использовать внешнюю PostgreSQL базу данных (опционально)
- Настроить резервное копирование volumes

### Production переменные окружения

Для production установите:

```env
# Безопасный SECRET_KEY (обязательно измените!)
SECRET_KEY=your-very-secure-random-secret-key-here

# Production база данных
SQLALCHEMY_URL=postgresql+asyncpg://user:password@db-host:5432/cyber_city

# ChromaDB Cloud (рекомендуется для production)
CHROMA_API_KEY=your-chroma-cloud-api-key
CHROMA_TENANT=your-chroma-tenant
CHROMA_DB_NAME=your-chroma-database-name

# OpenAI API
OPENAI_API_KEY=sk-your-production-api-key
OPENAI_MODEL=gpt-4  # или другой production модель
```

---

## Полезно для разработки

- **Логирование**:
    - backend‑сервисы (`auth`, `deps`, `seed`, `realtime`, `simulation`, `llm`) логируют ключевые операции,
    - удобно смотреть поведение агентов и ошибок в консоли сервера.
- **Расширяемость**:
    - легко добавить новые типы событий, эмоции, черты характера или отдельные «сцены» (групповые чаты).
    - модульная структура роутеров упрощает добавление новых эндпоинтов.
- **Безопасность**:
    - все пароли хэшируются с использованием bcrypt,
    - JWT токены имеют срок действия (настраивается в `settings.ACCESS_TOKEN_EXPIRE_MINUTES`),
    - проверка принадлежности ресурсов пользователю на уровне API.
- **Docker**:
    - все сервисы изолированы в контейнерах,
    - данные PostgreSQL сохраняются в Docker volumes,
    - легко масштабировать и развертывать.
