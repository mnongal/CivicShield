from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Need = Literal['food', 'housing', 'cash', 'work', 'transport']


class Situation(BaseModel):
    """Type hints and Field constraints turn untrusted JSON into validated data."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    borough: Literal['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island', 'Outside NYC']
    household_size: int = Field(ge=1, le=30)
    monthly_income: Decimal | None = Field(default=None, ge=0, le=10000000, decimal_places=2)
    annual_income: Decimal | None = Field(default=None, ge=0, le=120000000, decimal_places=2)
    age: int | None = Field(default=None, ge=0, le=120)
    needs: list[Need] = Field(min_length=1, max_length=5)
    housing_risk: bool | None = None
    job_loss: bool | None = None
    worked_in_ny: bool | None = None
    able_and_seeking_work: bool | None = None
