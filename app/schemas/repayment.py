from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class RepaymentCreate(BaseModel):
    loan_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    paid_at: date


class RepaymentUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    paid_at: date | None = None


class RepaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    loan_id: int
    member_id: int
    group_id: int
    amount: float
    paid_at: date
    recorded_by: int
