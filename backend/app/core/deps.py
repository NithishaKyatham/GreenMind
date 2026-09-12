"""
Shared FastAPI dependencies: current user extraction from JWT, admin guard.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import get_user_by_id


# Do not let HTTPBearer automatically return 403 when the header is missing.
# We want our API to return 401 Unauthorized instead.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # No Authorization header
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials

    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    user = get_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user