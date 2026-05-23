import uuid
from typing import TypedDict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Holding, Portfolio
from app.services.frankfurter import FrankfurterClientProtocol


class HoldingQuantity(TypedDict):
    currency_code: str
    quantity: float


def compute_portfolio_value_usd(
    holdings: list[HoldingQuantity],
    rates: dict[str, float],
) -> float:
    total = 0.0
    for holding in holdings:
        code = holding["currency_code"]
        quantity = holding["quantity"]
        if code == "USD":
            total += quantity
            continue
        rate = rates.get(code)
        if rate is None or rate == 0:
            raise ValueError(f"Missing or invalid rate for {code}")
        total += quantity / rate
    return round(total, 2)


def build_quantities_from_weights(
    total_usd: float,
    weights: list[tuple[str, float]],
    rates: dict[str, float],
) -> list[tuple[str, float, float]]:
    rows: list[tuple[str, float, float]] = []
    for currency_code, weight_percent in weights:
        notional_usd = total_usd * weight_percent / 100
        if currency_code == "USD":
            quantity = notional_usd
        else:
            rate = rates.get(currency_code)
            if rate is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Unsupported currency for allocation: {currency_code}",
                )
            quantity = notional_usd * rate
        rows.append((currency_code, weight_percent, round(quantity, 6)))
    return rows


def fetch_latest_rates(
    frankfurter: FrankfurterClientProtocol,
    currencies: list[str],
) -> tuple[str, dict[str, float]]:
    non_usd = sorted({code for code in currencies if code != "USD"})
    if not non_usd:
        return "", {}
    payload = frankfurter.fetch_latest("USD", non_usd)
    return payload["date"], payload["rates"]


def create_default_portfolio(db: Session) -> Portfolio:
    portfolio = Portfolio(
        id=str(uuid.uuid4()),
        initial_cash_usd=10000.0,
        prior_value_usd=10000.0,
        rates_date=None,
    )
    portfolio.holdings = [
        Holding(
            currency_code="USD",
            quantity=10000.0,
            weight_percent=100.0,
        )
    ]
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def get_portfolio_or_404(db: Session, portfolio_id: str) -> Portfolio:
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


def portfolio_to_response(
    portfolio: Portfolio,
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    holdings = portfolio.holdings
    currency_codes = [holding.currency_code for holding in holdings]
    rates_date, rates = fetch_latest_rates(frankfurter, currency_codes)
    quantities = [
        {"currency_code": holding.currency_code, "quantity": holding.quantity}
        for holding in holdings
    ]
    total_value = compute_portfolio_value_usd(quantities, rates)
    daily_pl = round(total_value - portfolio.prior_value_usd, 2)

    return {
        "id": portfolio.id,
        "initial_cash_usd": portfolio.initial_cash_usd,
        "total_value_usd": total_value,
        "daily_pl_usd": daily_pl,
        "rates_date": rates_date or portfolio.rates_date,
        "holdings": [
            {
                "currency_code": holding.currency_code,
                "weight_percent": holding.weight_percent,
                "quantity": holding.quantity,
            }
            for holding in holdings
        ],
    }


def update_portfolio_holdings(
    db: Session,
    portfolio: Portfolio,
    weights: list[tuple[str, float]],
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    currency_codes = [code for code, _ in weights]
    rates_date, rates = fetch_latest_rates(frankfurter, currency_codes)
    rows = build_quantities_from_weights(portfolio.initial_cash_usd, weights, rates)

    portfolio.holdings.clear()
    for currency_code, weight_percent, quantity in rows:
        portfolio.holdings.append(
            Holding(
                currency_code=currency_code,
                weight_percent=weight_percent,
                quantity=quantity,
            )
        )

    quantities = [{"currency_code": code, "quantity": qty} for code, _, qty in rows]
    current_value = compute_portfolio_value_usd(quantities, rates)
    portfolio.prior_value_usd = current_value
    portfolio.rates_date = rates_date or portfolio.rates_date
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio_to_response(portfolio, frankfurter)
