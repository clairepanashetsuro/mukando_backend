
from fastapi import HTTPException
from sqlalchemy import select

from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password


def create_member(db, treasurer, data):
    # Make sure the email is not already registered.
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

    # Members are created with a temporary password.
    # They must change this password after their first login.
    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.temporary_password),
        role=UserRole.MEMBER,
        group_id=treasurer.group_id,
        must_change_password=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_profile(db, user, data):
    # Prevent two users from having the same email.
    if (
        data.email
        and data.email != user.email
        and (
            db.execute(
                select(User).where(
                    User.email == data.email,
                    User.id != user.id,
                )
            )
            .scalar_one_or_none()
        )
    ):
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    # Update only fields supplied by the client.
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


def change_password(db, user, current_password, new_password):
    # The user must know their current password.
    if not verify_password(
        current_password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    # Store only the hashed version of the new password.
    user.password_hash = hash_password(new_password)

    # This also completes the initial member password-change
    # requirement if the user was created with a temporary password.
    user.must_change_password = False

    db.commit()

