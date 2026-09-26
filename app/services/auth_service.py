
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.group import Group
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken

from app.core.security import (
    hash_password,
    verify_password,
    create_token,
    hash_token,
    new_random_token,
    decode_token,
)

from app.core.config import settings
from app.services.email_service import send_password_reset_email


def _expired(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value < datetime.now(timezone.utc)


def signup_treasurer(db, data):
    # Check whether email already exists
    existing_user = (
        db.execute(
            select(User).where(User.email == data.email)
        )
        .scalar_one_or_none()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    # Check whether group name already exists
    existing_group = (
        db.execute(
            select(Group).where(Group.name == data.group_name)
        )
        .scalar_one_or_none()
    )

    if existing_group:
        raise HTTPException(
            status_code=409,
            detail="Group name already exists",
        )

    group = Group(
        name=data.group_name,
        weekly_contribution=data.weekly_contribution,
    )

    db.add(group)
    db.flush()

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.TREASURER,
        group_id=group.id,
    )

    db.add(user)
    db.flush()
    db.commit()

    return user


def authenticate(db, email, password):
    user = (
        db.execute(
            select(User).where(User.email == email)
        )
        .scalar_one_or_none()
    )

    if not user or not verify_password(
        password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive",
        )

    return user


def issue_tokens(db, user):
    access, access_exp = create_token(
        str(user.id),
        user.role.value,
        "access",
        settings.access_token_expire_minutes,
    )

    refresh, refresh_exp = create_token(
        str(user.id),
        user.role.value,
        "refresh",
        settings.refresh_token_expire_minutes,
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh),
            expires_at=refresh_exp,
        )
    )

    db.commit()

    return access, refresh


def refresh(db, token):
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    rt = (
        db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(token)
            )
        )
        .scalar_one_or_none()
    )

    if not rt or rt.revoked or _expired(rt.expires_at):
        raise HTTPException(
            status_code=401,
            detail="Refresh token revoked or expired",
        )

    user = (
        db.execute(
            select(User).where(
                User.id == int(payload["sub"])
            )
        )
        .scalar_one_or_none()
    )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User inactive",
        )

    rt.revoked = True
    db.flush()

    return issue_tokens(db, user)


def logout(db, token):
    rt = (
        db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(token)
            )
        )
        .scalar_one_or_none()
    )

    if rt:
        rt.revoked = True
        db.commit()


def forgot_password(db, email):
    user = (
        db.execute(
            select(User).where(User.email == email)
        )
        .scalar_one_or_none()
    )

    # Do not reveal whether an email exists
    if not user:
        return

    # Generate a dedicated password-reset token
    raw_token = new_random_token()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=settings.password_reset_expire_minutes
        )
    )

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=expires_at,
        used=False,
    )

    db.add(reset_token)
    db.commit()

    # Send the raw token to the user's email.
    # Only the hash is stored in the database.
    send_password_reset_email(
        email,
        raw_token,
    )


def reset_password(db, token, new_password):
    # Hash the token supplied by the user and
    # compare it with the stored hash.
    row = (
        db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == hash_token(token)
            )
        )
        .scalar_one_or_none()
    )

    # Token must exist, not be used, and not be expired.
    if not row or row.used or _expired(row.expires_at):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        )

    user = (
        db.execute(
            select(User).where(
                User.id == row.user_id
            )
        )
        .scalar_one_or_none()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Set the new password
    user.password_hash = hash_password(new_password)

    # A successful reset also satisfies
    # any pending first-login password requirement.
    user.must_change_password = False

    # Make the reset token single-use.
    row.used = True

    # Revoke existing refresh tokens.
    # This forces existing sessions to authenticate again.
    refresh_tokens = (
        db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked == False,
            )
        )
        .scalars()
        .all()
    )

    for refresh_token in refresh_tokens:
        refresh_token.revoked = True

    db.commit()

