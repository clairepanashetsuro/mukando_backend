from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from app.models.loan import LoanStatus


class LoanCreate(BaseModel):
    member_id: int = Field(gt=0)
    principal: float = Field(gt=0)
    due_date: date


class LoanUpdate(BaseModel):
    due_date: date | None = None
    status: LoanStatus | None = None


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    group_id: int
    principal: float
    interest_rate: float
    interest_amount: float
    due_date: date
    status: LoanStatus
