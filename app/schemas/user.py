from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TreasurerSignup(UserCreate):
    group_name: str = Field(min_length=2, max_length=150)
    weekly_contribution: float = Field(default=0, ge=0)


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    temporary_password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    group_id: int | None
    must_change_password: bool
    is_active: bool
