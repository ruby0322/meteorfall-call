from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps.db import DbSession
from app.schemas.portfolio import (
    CreatePortfolioRequest,
    PortfolioHistoryResponse,
    PortfolioResponse,
    PortfolioSnapshotResponse,
    PortfolioTransactionsResponse,
    PreviewHoldingsResponse,
    UpdateBaseCurrencyRequest,
    UpdateHoldingsRequest,
)
from app.services.frankfurter import FrankfurterClientProtocol
from app.services.portfolio import (
    create_default_portfolio,
    get_portfolio_or_404,
    portfolio_history_response,
    portfolio_snapshot_response,
    portfolio_to_response,
    portfolio_transactions_response,
    preview_portfolio_holdings,
    switch_portfolio_base_currency,
    update_portfolio_holdings,
)

router = APIRouter(prefix="/v1", tags=["portfolio"])


def get_frankfurter(request: Request) -> FrankfurterClientProtocol:
    return request.app.state.frankfurter


@router.post("/portfolio", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
    payload: CreatePortfolioRequest | None = None,
) -> dict:
    portfolio = create_default_portfolio(db, payload.base_currency if payload else "USD")
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


@router.get("/portfolio/{portfolio_id}/snapshot", response_model=PortfolioSnapshotResponse)
def portfolio_snapshot(
    portfolio_id: str,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    return portfolio_snapshot_response(portfolio, frankfurter)


@router.get("/portfolio/{portfolio_id}/transactions", response_model=PortfolioTransactionsResponse)
def portfolio_transactions(
    portfolio_id: str,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    return portfolio_transactions_response(portfolio, frankfurter)


@router.patch("/portfolio/{portfolio_id}/base-currency", response_model=PortfolioResponse)
def update_portfolio_base_currency(
    portfolio_id: str,
    payload: UpdateBaseCurrencyRequest,
    db: DbSession,
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
) -> dict:
    portfolio = get_portfolio_or_404(db, portfolio_id)
    return switch_portfolio_base_currency(db, portfolio, payload.base_currency, frankfurter)
