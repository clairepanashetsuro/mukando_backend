
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import TreasurerSignup

from app.schemas.auth import (
    TokenResponse,
    AuthResponse,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

from app.services.auth_service import (
    signup_treasurer,
    authenticate,
    issue_tokens,
    refresh,
    logout,
    forgot_password,
    reset_password,
)

from app.dependencies import DB
from app.core.config import settings


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def token_response(tokens):
    return TokenResponse(
        access_token=tokens[0],
        refresh_token=tokens[1],
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
)
def signup(
    data: TreasurerSignup,
    db: DB,
):
    user = signup_treasurer(db, data)

    tokens = issue_tokens(db, user)

    return AuthResponse(
        user=user,
        tokens=token_response(tokens),
    )


@router.post("/login")
def login(
    db: DB,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate(
        db,
        form_data.username,
        form_data.password,
    )

    tokens = issue_tokens(db, user)

    return {
        "access_token": tokens[0],
        "refresh_token": tokens[1],
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    data: RefreshRequest,
    db: DB,
):
    return token_response(
        refresh(
            db,
            data.refresh_token,
        )
    )


@router.post(
    "/logout",
    status_code=204,
)
def logout_endpoint(
    data: RefreshRequest,
    db: DB,
):
    logout(
        db,
        data.refresh_token,
    )


@router.post(
    "/forgot-password",
    status_code=202,
)
def forgot(
    data: ForgotPasswordRequest,
    db: DB,
):
    forgot_password(
        db,
        data.email,
    )


@router.post(
    "/reset-password",
    status_code=204,
)
def reset(
    data: ResetPasswordRequest,
    db: DB,
):
    reset_password(
        db,
        data.token,
        data.new_password,
    )

