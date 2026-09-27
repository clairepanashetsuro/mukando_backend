from datetime import date, datetime
from sqlalchemy import Date, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
class Repayment(Base):
    __tablename__="repayments"
    id: Mapped[int]=mapped_column(primary_key=True)
    loan_id: Mapped[int]=mapped_column(ForeignKey("loans.id"), index=True)
    member_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int]=mapped_column(ForeignKey("groups.id"), index=True)
    amount: Mapped[float]=mapped_column(Numeric(12,2))
    paid_at: Mapped[date]=mapped_column(Date)
    recorded_by: Mapped[int]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=datetime.utcnow)
