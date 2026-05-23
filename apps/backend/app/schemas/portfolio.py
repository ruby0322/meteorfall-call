from pydantic import BaseModel, Field, field_validator


class HoldingInput(BaseModel):
    currency_code: str = Field(min_length=3, max_length=3)
    weight_percent: float = Field(gt=0, le=100)

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class CreatePortfolioRequest(BaseModel):
    base_currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("base_currency")
    @classmethod
    def uppercase_base_currency(cls, value: str) -> str:
        return value.upper()


class UpdateBaseCurrencyRequest(BaseModel):
    base_currency: str = Field(min_length=3, max_length=3)

    @field_validator("base_currency")
    @classmethod
    def uppercase_base_currency(cls, value: str) -> str:
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


class HoldingDetailResponse(HoldingResponse):
    usd_value: float
    weight_actual_percent: float


class HoldingDeltaResponse(BaseModel):
    currency_code: str
    quantity_delta: float
    usd_delta: float


class PortfolioResponse(BaseModel):
    id: str
    base_currency: str
    initial_cash_usd: float
    total_value_usd: float
    daily_pl_usd: float
    rates_date: str | None
    prior_rates_date: str | None
    holdings: list[HoldingResponse]
    holdings_detail: list[HoldingDetailResponse]


class PreviewHoldingsResponse(BaseModel):
    base_currency: str
    total_value_usd: float
    projected_holdings: list[HoldingDetailResponse]
    deltas: list[HoldingDeltaResponse]


class PortfolioHistoryPointResponse(BaseModel):
    date: str
    total_value_usd: float
    daily_pl_usd: float


class PortfolioHistoryResponse(BaseModel):
    base_currency: str
    points: list[PortfolioHistoryPointResponse]
    rebalance_markers: list[str]


class PortfolioSnapshotResponse(BaseModel):
    base_currency: str
    as_of: str | None
    total_value_usd: float
    daily_pl_usd: float
    holdings: list[HoldingDetailResponse]
    disclaimer: str


class PortfolioTransactionHoldingResponse(BaseModel):
    currency_code: str
    weight_percent: float
    quantity: float


class PortfolioTransactionResponse(BaseModel):
    id: int
    event_type: str
    base_currency: str
    effective_rates_date: str
    total_value_usd: float
    holdings: list[PortfolioTransactionHoldingResponse]
    created_at: str


class PortfolioTransactionsResponse(BaseModel):
    base_currency: str
    transactions: list[PortfolioTransactionResponse]
