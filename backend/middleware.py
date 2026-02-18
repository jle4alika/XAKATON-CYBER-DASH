"""
Middleware for user authentication and authorization
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgr.db import get_session
from backend.services.auth import verify_token
from backend.project_config import settings


async def auth_middleware(request: Request, call_next):
    """
    Middleware to check user authentication based on JWT token
    """
    # Skip authentication for login/register and public endpoints
    excluded_paths = ["/api/auth/login", "/api/auth/register", "/docs", "/openapi.json"]
    if request.url.path in excluded_paths or request.url.path.startswith("/static"):
        response = await call_next(request)
        return response

    # Get authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid authorization header"}
        )

    token = auth_header.split(" ")[1]

    # Verify token
    try:
        async with get_session() as session:
            user = await verify_token(session, token)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token"}
                )

            # Add user to request state for use in route handlers
            request.state.user = user
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Could not validate credentials"}
        )

    response = await call_next(request)
    return response
