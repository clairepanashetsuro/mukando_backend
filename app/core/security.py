
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(
    subject: str,
    role: str,
    token_type: str,
    expires_minutes: int,
    extra: dict | None = None,
) -> tuple[str, datetime]:

    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)

    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": exp,
        "jti": secrets.token_urlsafe(32),
        **(extra or {}),
    }

    return (
        jwt.encode(
            payload,
            settings.private_key(),
            algorithm=settings.jwt_algorithm,
        ),
        exp,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.public_key(),
        algorithms=[settings.jwt_algorithm],
    )


def new_random_token() -> str:
    return secrets.token_urlsafe(48)

