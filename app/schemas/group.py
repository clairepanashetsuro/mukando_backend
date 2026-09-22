from pydantic import BaseModel, ConfigDict, Field


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    weekly_contribution: float | None = Field(default=None, ge=0)


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    weekly_contribution: float
