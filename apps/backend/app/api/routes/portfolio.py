from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps.db import DbSession
from app.schemas.portfolio import (
    PortfolioHistoryResponse,
    PortfolioResponse,
    PreviewHoldingsResponse,
    UpdateHoldingsRequest,
)
from app.services.frankfurter import FrankfurterClientProtocol
from app.services.portfolio import (
    create_default_portfolio,
    get_portfolio_or_404,
    portfolio_history_response,
    portfolio_to_response,
    preview_portfolio_holdings,
    update_portfolio_holdings,
)

router = APIRouter(prefix="/v1", tags=["portfolio"])


def get_frankfurter(request: Request) -> FrankfurterClientProtocol:
    return request.app.state.frankfurter


@router.post("/portfolio", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = create_default_portfolio(db)
    return portfolio_to_response(portfolio, frankfurter)


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: str,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    return portfolio_to_response(portfolio, frankfurter)


@router.put("/portfolio/{portfolio_id}/holdings", response_model=PortfolioResponse)
def replace_portfolio_holdings(
    portfolio_id: str,
    payload: UpdateHoldingsRequest,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    weights = [(item.currency_code, item.weight_percent) for item in payload.holdings]
    return update_portfolio_holdings(db, portfolio, weights, frankfurter)


@router.post("/portfolio/{portfolio_id}/holdings/preview", response_model=PreviewHoldingsResponse)
def preview_holdings(
    portfolio_id: str,
    payload: UpdateHoldingsRequest,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    weights = [(item.currency_code, item.weight_percent) for item in payload.holdings]
    return preview_portfolio_holdings(portfolio, weights, frankfurter)


@router.get("/portfolio/{portfolio_id}/history", response_model=PortfolioHistoryResponse)
def portfolio_history(
    portfolio_id: str,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
    days: int = 30,
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    return portfolio_history_response(portfolio, days, frankfurter)
