from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
class UserRole(str, Enum): TREASURER="TREASURER"; MEMBER="MEMBER"
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    full_name: Mapped[str]=mapped_column(String(150))
    email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[UserRole]=mapped_column(SAEnum(UserRole), index=True)
    group_id: Mapped[int|None]=mapped_column(ForeignKey("groups.id"), nullable=True, index=True)
    must_change_password: Mapped[bool]=mapped_column(Boolean, default=False)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
