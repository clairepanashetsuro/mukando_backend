from datetime import datetime
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
class Group(Base):
    __tablename__="groups"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(150), unique=True)
    weekly_contribution: Mapped[float]=mapped_column(Numeric(12,2), default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.utcnow)
