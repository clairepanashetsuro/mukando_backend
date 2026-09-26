
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

DB = Annotated[Session, Depends(get_db)]


def current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DB,
):
    try:
        # Decode and verify the JWT.
        payload = decode_token(token)

        # Make sure this is an access token,
        # not a refresh token or another token type.
        if payload.get("type") != "access":
            raise ValueError(
                f"Wrong token type: {payload.get('type')}"
            )

        # Get the user ID from the JWT subject.
        user_id = int(payload["sub"])

    except Exception as e:
        # Temporarily expose the actual JWT error
        # so we can identify the cause.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token error: {str(e)}",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # Load the user from the database.
    from app.repositories.user_repository import user_repository

    user = user_repository.get(db, user_id)

    # Make sure the user still exists and is active.
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    return user


CurrentUser = Annotated[
    object,
    Depends(current_user),
]


def require_role(role: str):
    def dependency(user: CurrentUser):
        if user.role.value != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return user

    return dependency

