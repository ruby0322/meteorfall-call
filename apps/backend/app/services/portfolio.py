import json
import uuid
from datetime import date, timedelta
from typing import TypedDict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Holding, Portfolio, RebalanceRecord
from app.services.frankfurter import FrankfurterClientProtocol


class HoldingQuantity(TypedDict):
    currency_code: str
    quantity: float


class HoldingDetail(TypedDict):
    currency_code: str
    weight_percent: float
    weight_actual_percent: float
    quantity: float
    usd_value: float


class HistoryPoint(TypedDict):
    date: str
    total_value_usd: float
    daily_pl_usd: float
    cumulative_pl_usd: float


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


def _to_quantities(holdings: list[Holding]) -> list[HoldingQuantity]:
    return [
        {"currency_code": holding.currency_code, "quantity": holding.quantity}
        for holding in holdings
    ]


def _rows_from_holdings(holdings: list[Holding]) -> list[tuple[str, float, float]]:
    return [(holding.currency_code, holding.weight_percent, holding.quantity) for holding in holdings]


def _snapshot_rows(rows: list[tuple[str, float, float]]) -> str:
    return json.dumps(
        [
            {"currency_code": code, "weight_percent": weight, "quantity": quantity}
            for code, weight, quantity in rows
        ]
    )


def _parse_snapshot_rows(serialized_rows: str) -> list[tuple[str, float, float]]:
    parsed = json.loads(serialized_rows)
    return [
        (str(item["currency_code"]), float(item["weight_percent"]), float(item["quantity"]))
        for item in parsed
    ]


def _ensure_rebalance_record(
    db: Session,
    portfolio: Portfolio,
    rates_date: str,
    total_value_usd: float,
    rows: list[tuple[str, float, float]],
) -> None:
    db.add(
        RebalanceRecord(
            portfolio_id=portfolio.id,
            effective_rates_date=rates_date,
            total_value_usd=round(total_value_usd, 2),
            holdings_json=_snapshot_rows(rows),
        )
    )


def _resolve_usd_value(currency_code: str, quantity: float, rates: dict[str, float]) -> float:
    if currency_code == "USD":
        return round(quantity, 2)
    rate = rates.get(currency_code)
    if rate is None or rate == 0:
        raise ValueError(f"Missing or invalid rate for {currency_code}")
    return round(quantity / rate, 2)


def _build_holding_details(
    rows: list[tuple[str, float, float]],
    total_value_usd: float,
    rates: dict[str, float],
) -> list[HoldingDetail]:
    details: list[HoldingDetail] = []
    for currency_code, weight_percent, quantity in rows:
        usd_value = _resolve_usd_value(currency_code, quantity, rates)
        actual_weight = 0.0 if total_value_usd == 0 else round(usd_value / total_value_usd * 100, 2)
        details.append(
            {
                "currency_code": currency_code,
                "weight_percent": round(weight_percent, 4),
                "weight_actual_percent": actual_weight,
                "quantity": round(quantity, 6),
                "usd_value": usd_value,
            }
        )
    return details


def _find_prior_business_day_rates(
    frankfurter: FrankfurterClientProtocol,
    currencies: list[str],
    current_rates_date: str,
) -> tuple[str | None, dict[str, float]]:
    non_usd = sorted({code for code in currencies if code != "USD"})
    if not non_usd:
        return None, {}

    end_day = date.fromisoformat(current_rates_date)
    start_day = end_day - timedelta(days=10)
    payload = frankfurter.fetch_history("USD", non_usd, start_day.isoformat(), end_day.isoformat())
    rates_by_date = payload.get("rates", {})
    available_dates = sorted(rates_by_date.keys())

    prior_dates = [day for day in available_dates if day < current_rates_date]
    if not prior_dates:
        return None, {}

    prior_date = prior_dates[-1]
    prior_rates = rates_by_date.get(prior_date, {})
    return prior_date, prior_rates


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
    _ensure_rebalance_record(
        db=db,
        portfolio=portfolio,
        rates_date=date.today().isoformat(),
        total_value_usd=portfolio.initial_cash_usd,
        rows=[("USD", 100.0, portfolio.initial_cash_usd)],
    )
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
    quantities = _to_quantities(holdings)
    total_value = compute_portfolio_value_usd(quantities, rates)
    rows = [(holding.currency_code, holding.weight_percent, holding.quantity) for holding in holdings]

    prior_rates_date: str | None = None
    prior_total_value = total_value
    if rates_date:
        prior_rates_date, prior_rates = _find_prior_business_day_rates(
            frankfurter, currency_codes, rates_date
        )
        if prior_rates_date:
            prior_total_value = compute_portfolio_value_usd(quantities, prior_rates)

    daily_pl = round(total_value - prior_total_value, 2)
    cumulative_pl = round(total_value - portfolio.initial_cash_usd, 2)
    holdings_detail = _build_holding_details(rows, total_value, rates)

    return {
        "id": portfolio.id,
        "initial_cash_usd": portfolio.initial_cash_usd,
        "total_value_usd": total_value,
        "daily_pl_usd": daily_pl,
        "cumulative_pl_usd": cumulative_pl,
        "rates_date": rates_date or portfolio.rates_date,
        "prior_rates_date": prior_rates_date,
        "holdings": [
            {
                "currency_code": holding.currency_code,
                "weight_percent": holding.weight_percent,
                "quantity": holding.quantity,
            }
            for holding in holdings
        ],
        "holdings_detail": holdings_detail,
    }


def preview_portfolio_holdings(
    portfolio: Portfolio,
    weights: list[tuple[str, float]],
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    existing_rows = _rows_from_holdings(portfolio.holdings)
    existing_quantities = _to_quantities(portfolio.holdings)
    existing_currency_codes = [holding.currency_code for holding in portfolio.holdings]
    existing_rates_date, existing_rates = fetch_latest_rates(frankfurter, existing_currency_codes)
    current_total = compute_portfolio_value_usd(existing_quantities, existing_rates)

    preview_currency_codes = [code for code, _ in weights]
    _, preview_rates = fetch_latest_rates(frankfurter, preview_currency_codes)
    preview_rows = build_quantities_from_weights(current_total, weights, preview_rates)
    projected_quantities = [{"currency_code": code, "quantity": qty} for code, _, qty in preview_rows]
    projected_total = compute_portfolio_value_usd(projected_quantities, preview_rates)
    projected_details = _build_holding_details(preview_rows, projected_total, preview_rates)

    by_currency_current = {
        currency_code: {"quantity": quantity, "usd_value": _resolve_usd_value(currency_code, quantity, existing_rates)}
        for currency_code, _, quantity in existing_rows
    }
    by_currency_projected = {item["currency_code"]: item for item in projected_details}
    currencies = sorted(set(by_currency_current.keys()) | set(by_currency_projected.keys()))
    deltas = []
    for code in currencies:
        current_quantity = by_currency_current.get(code, {}).get("quantity", 0.0)
        current_usd = by_currency_current.get(code, {}).get("usd_value", 0.0)
        projected_quantity = by_currency_projected.get(code, {}).get("quantity", 0.0)
        projected_usd = by_currency_projected.get(code, {}).get("usd_value", 0.0)
        deltas.append(
            {
                "currency_code": code,
                "quantity_delta": round(projected_quantity - current_quantity, 6),
                "usd_delta": round(projected_usd - current_usd, 2),
            }
        )

    return {
        "total_value_usd": projected_total,
        "projected_holdings": projected_details,
        "deltas": deltas,
        "rates_date": existing_rates_date,
    }


def update_portfolio_holdings(
    db: Session,
    portfolio: Portfolio,
    weights: list[tuple[str, float]],
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    existing_quantities = _to_quantities(portfolio.holdings)
    existing_currency_codes = [holding.currency_code for holding in portfolio.holdings]
    _, existing_rates = fetch_latest_rates(frankfurter, existing_currency_codes)
    current_total = compute_portfolio_value_usd(existing_quantities, existing_rates)

    preview_currency_codes = [code for code, _ in weights]
    rates_date, rates = fetch_latest_rates(frankfurter, preview_currency_codes)
    rows = build_quantities_from_weights(current_total, weights, rates)

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
    _ensure_rebalance_record(
        db=db,
        portfolio=portfolio,
        rates_date=rates_date or date.today().isoformat(),
        total_value_usd=current_value,
        rows=rows,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio_to_response(portfolio, frankfurter)


def portfolio_history_response(
    portfolio: Portfolio,
    days: int,
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    if days < 2:
        days = 2

    records = list(portfolio.rebalance_records)
    if not records:
        rows = _rows_from_holdings(portfolio.holdings)
        records = [
            RebalanceRecord(
                portfolio_id=portfolio.id,
                effective_rates_date=(portfolio.rates_date or date.today().isoformat()),
                total_value_usd=portfolio.initial_cash_usd,
                holdings_json=_snapshot_rows(rows),
            )
        ]

    records = sorted(records, key=lambda item: (item.effective_rates_date, item.created_at))
    latest_history_date = date.today().isoformat()
    if portfolio.rates_date:
        latest_history_date = portfolio.rates_date
    else:
        current_rates_date, _ = fetch_latest_rates(
            frankfurter, [holding.currency_code for holding in portfolio.holdings]
        )
        latest_history_date = current_rates_date or latest_history_date

    end_day = date.fromisoformat(latest_history_date)
    start_day = end_day - timedelta(days=days + 10)
    points_by_date: dict[str, float] = {}
    markers: list[str] = []

    for index, record in enumerate(records):
        segment_start = max(date.fromisoformat(record.effective_rates_date), start_day)
        next_effective = (
            date.fromisoformat(records[index + 1].effective_rates_date)
            if index + 1 < len(records)
            else end_day + timedelta(days=1)
        )
        segment_end = min(end_day, next_effective - timedelta(days=1))
        if segment_end < segment_start:
            continue

        rows = _parse_snapshot_rows(record.holdings_json)
        quantities = [{"currency_code": code, "quantity": qty} for code, _, qty in rows]
        non_usd = sorted({code for code, _, _ in rows if code != "USD"})

        if segment_start <= end_day and record.effective_rates_date >= start_day.isoformat():
            markers.append(record.effective_rates_date)

        if not non_usd:
            points_by_date[segment_start.isoformat()] = round(sum(qty for code, _, qty in rows if code == "USD"), 2)
            continue

        payload = frankfurter.fetch_history(
            "USD", non_usd, segment_start.isoformat(), segment_end.isoformat()
        )
        rates_by_date = payload.get("rates", {})
        for day in sorted(rates_by_date.keys()):
            rates = rates_by_date.get(day, {})
            points_by_date[day] = compute_portfolio_value_usd(quantities, rates)

    sorted_dates = sorted(day for day in points_by_date.keys() if day >= start_day.isoformat())
    points: list[HistoryPoint] = []
    previous_value: float | None = None
    for day in sorted_dates:
        value = points_by_date[day]
        daily_pl = 0.0 if previous_value is None else round(value - previous_value, 2)
        points.append(
            {
                "date": day,
                "total_value_usd": value,
                "daily_pl_usd": daily_pl,
                "cumulative_pl_usd": round(value - portfolio.initial_cash_usd, 2),
            }
        )
        previous_value = value

    return {"points": points, "rebalance_markers": sorted(set(markers))}


def portfolio_snapshot_response(
    portfolio: Portfolio,
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    current = portfolio_to_response(portfolio, frankfurter)
    return {
        "as_of": current["rates_date"],
        "total_value_usd": current["total_value_usd"],
        "daily_pl_usd": current["daily_pl_usd"],
        "cumulative_pl_usd": current["cumulative_pl_usd"],
        "holdings": current["holdings_detail"],
        "disclaimer": "Simulation only. Not investment advice.",
    }
