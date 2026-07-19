from collections.abc import Callable
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from shared.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


class User(BaseModel):
    id: str
    email: Optional[str] = None
    role: str = "researcher"


def _authentication_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication is not configured for this environment.",
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """Validate a Supabase-issued user token before serving the laboratory API."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_PUBLISHABLE_KEY:
        raise _authentication_unavailable()

    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        async with httpx.AsyncClient(timeout=settings.SUPABASE_AUTH_TIMEOUT_SECONDS) as client:
            response = await client.get(
                settings.supabase_auth_url,
                headers={
                    "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
                    "Authorization": f"Bearer {credentials.credentials}",
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        ) from exc

    if response.status_code != status.HTTP_200_OK:
        if 400 <= response.status_code < 500:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The access token is invalid or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        )

    payload = response.json()
    user_id = payload.get("id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token does not identify a user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # app_metadata is server-controlled in Supabase; user_metadata must never set roles.
    app_metadata = payload.get("app_metadata") or {}
    role = app_metadata.get("lab_role", "researcher")
    if role not in {"researcher", "reviewer", "administrator"}:
        role = "researcher"

    return User(id=user_id, email=payload.get("email"), role=role)


def require_roles(*allowed_roles: str) -> Callable:
    async def require_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your laboratory role does not permit this operation.",
            )
        return user

    return require_role