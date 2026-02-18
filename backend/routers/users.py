# ---------------------------------------------------------
# Роутер для управления пользователями
# ---------------------------------------------------------

from fastapi import APIRouter, Depends

from backend.database.postgr.models import User
from backend.schemas import UserResponse
from backend.services.deps import get_current_active_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        registered_time=current_user.registered_time
    )
