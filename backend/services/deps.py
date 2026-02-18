"""
Dependencies for FastAPI routes.
Здесь собраны зависимости, которые переиспользуются в обработчиках (получение текущего пользователя и т.п.).
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgr.db import get_session
from backend.database.postgr.models import User
from backend.project_config import settings
from backend.schemas import TokenData
from backend.services.auth import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
logger = logging.getLogger(__name__)


async def get_current_user(
        session: AsyncSession = Depends(get_session),
        token: str = Depends(oauth2_scheme),
) -> User:
    """
    Получить текущего пользователя на основе JWT-токена.

    Используется как базовая зависимость для защищённых маршрутов.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Ошибка декодирования JWT: отсутствует 'sub' в payload")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as exc:
        logger.warning("Ошибка декодирования JWT: %s", exc)
        raise credentials_exception

    user = await get_user_by_username(session, username=token_data.username)
    if user is None:
        logger.warning("Пользователь по JWT не найден: %s", token_data.username)
        raise credentials_exception

    logger.debug("Текущий пользователь аутентифицирован id=%s username=%s", user.id, user.username)
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Получить текущего "активного" пользователя.

    Сейчас просто проксирует get_current_user, но сюда можно добавить бизнес-проверки
    (например, заблокированные пользователи, флаги is_active и т.п.).
    """
    # Пример будущей проверки:
    # if current_user.disabled:
    #     logger.info("Inactive user tried to access protected resource: %s", current_user.id)
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
