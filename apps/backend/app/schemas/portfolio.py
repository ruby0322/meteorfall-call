from pydantic import BaseModel, Field, field_validator


class HoldingInput(BaseModel):
    currency_code: str = Field(min_length=3, max_length=3)
    weight_percent: float = Field(gt=0, le=100)

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class UpdateHoldingsRequest(BaseModel):
    holdings: list[HoldingInput] = Field(min_length=1)

    @field_validator("holdings")
    @classmethod
    def weights_sum_to_one_hundred(cls, holdings: list[HoldingInput]) -> list[HoldingInput]:
        total = round(sum(item.weight_percent for item in holdings), 4)
        if total != 100.0:
            raise ValueError("holdings weights must sum to 100")
        return holdings


class HoldingResponse(BaseModel):
    currency_code: str
    weight_percent: float
    quantity: float


class PortfolioResponse(BaseModel):
    id: str
    initial_cash_usd: float
    total_value_usd: float
    daily_pl_usd: float
    rates_date: str | None
    holdings: list[HoldingResponse]
