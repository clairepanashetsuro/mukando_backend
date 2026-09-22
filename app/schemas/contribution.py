from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ContributionCreate(BaseModel):
    member_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    paid_at: date


class ContributionUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    paid_at: date | None = None


class ContributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    group_id: int
    amount: float
    paid_at: date
    recorded_by: int
