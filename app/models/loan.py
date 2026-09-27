from datetime import date, datetime
from enum import Enum
from sqlalchemy import Date, Numeric, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
class LoanStatus(str, Enum): ACTIVE="ACTIVE"; PAID="PAID"; DEFAULTED="DEFAULTED"
class Loan(Base):
    __tablename__="loans"
    id: Mapped[int]=mapped_column(primary_key=True)
    member_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int]=mapped_column(ForeignKey("groups.id"), index=True)
    principal: Mapped[float]=mapped_column(Numeric(12,2))
    interest_rate: Mapped[float]=mapped_column(Numeric(5,2), default=10)
    interest_amount: Mapped[float]=mapped_column(Numeric(12,2))
    due_date: Mapped[date]=mapped_column(Date)
    status: Mapped[LoanStatus]=mapped_column(SAEnum(LoanStatus), default=LoanStatus.ACTIVE)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.utcnow)
