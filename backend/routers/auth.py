# ---------------------------------------------------------
# Роутер для аутентификации и управления пользователями
# ---------------------------------------------------------

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgr.db import get_session
from backend.database.postgr.models import User
from backend.project_config import settings
from backend.schemas import UserCreate, UserLogin, Token, UserResponse
from backend.services.auth import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    authenticate_user,
    create_access_token,
)
from backend.services.deps import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new user"""
    logger.info("Запрос регистрации пользователя: username=%s, email=%s", user_data.username, user_data.email)
    # Check if username already exists
    existing_user = await get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = await get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = await create_user(session, user_data)
    logger.info("Пользователь зарегистрирован id=%s username=%s", user.id, user.username)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        registered_time=user.registered_time
    )


@router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin, session: AsyncSession = Depends(get_session)):
    """Authenticate user and return JWT token"""
    logger.info("Попытка входа пользователя username=%s", user_data.username)
    user = await authenticate_user(session, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info("Успешный вход пользователя username=%s", user.username)
    return {"access_token": access_token, "token_type": "bearer"}
