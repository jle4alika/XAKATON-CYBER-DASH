"""
Authentication service for user registration, login and JWT token management.
Содержит вспомогательные функции для работы с пользователями и JWT.
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.database.postgr.models import User, GroupChat
from backend.project_config import settings
from backend.schemas import UserCreate, UserLogin, TokenData

logger = logging.getLogger(__name__)


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    """
    Получить пользователя по username.

    Возвращает ORM-объект User или None, если пользователь не найден.
    """
    logger.debug("Поиск пользователя по username=%s", username)
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        logger.debug("Пользователь с username=%s не найден", username)
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """
    Получить пользователя по e-mail.

    Используется для проверки уникальности почты при регистрации.
    """
    logger.debug("Поиск пользователя по email=%s", email)
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        logger.debug("Пользователь с email=%s не найден", email)
    return user


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """
    Создать нового пользователя с захешированным паролем и дефолтным групповым чатом.

    Сначала создаётся запись User, затем для него создаётся групповой чат
    «Кибер город», который используется как базовая сцена для агентов.
    """
    logger.info("Создание пользователя: username=%s, email=%s", user_data.username, user_data.email)

    # Хешируем пароль перед сохранением
    hashed_password = bcrypt.hashpw(user_data.password.encode("utf-8"), bcrypt.gensalt())

    # Создаём пользователя
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password.decode("utf-8"),
    )

    session.add(user)
    await session.flush()  # Получаем ID пользователя до коммита

    # Создаём дефолтный групповой чат для этого пользователя
    default_chat = GroupChat(
        name="Кибер город",
        description="Город, в котором живут ваши агенты",
        created_by_user_id=user.id,
        is_active=True,
    )

    session.add(default_chat)
    await session.commit()
    await session.refresh(user)

    logger.info("Пользователь создан id=%s, создан дефолтный чат id=%s", user.id, default_chat.id)
    return user


async def authenticate_user(session: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    Аутентифицировать пользователя по username и паролю.

    Возвращает пользователя при успехе или None при ошибке.
    """
    logger.debug("Аутентификация пользователя username=%s", username)
    user = await get_user_by_username(session, username)
    if not user:
        logger.warning("Ошибка аутентификации: пользователь %s не найден", username)
        return None

    # Проверяем пароль
    if bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        logger.info("Успешная аутентификация пользователя username=%s", username)
        return user

    logger.warning("Ошибка аутентификации: неверный пароль для username=%s", username)
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создать JWT access-токен.

    В payload ожидается ключ "sub" (subject) — обычно username пользователя.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug("Создан access-токен для sub=%s", data.get("sub"))
    return encoded_jwt


async def verify_token(session: AsyncSession, token: str) -> Optional[User]:
    """
    Проверить JWT-токен и вернуть пользователя.

    Возвращает None, если токен недействителен или пользователь не найден.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Проверка токена не удалась: нет 'sub' в payload")
            return None
        token_data = TokenData(username=username)
    except JWTError as exc:
        logger.warning("Проверка токена не удалась: %s", exc)
        return None

    user = await get_user_by_username(session, username=token_data.username)
    if not user:
        logger.warning("Проверка токена не удалась: пользователь %s не найден", token_data.username)
    return user
