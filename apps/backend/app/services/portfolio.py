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


def compute_portfolio_value_in_base(
    holdings: list[HoldingQuantity],
    rates: dict[str, float],
    base_currency: str,
) -> float:
    total = 0.0
    for holding in holdings:
        code = holding["currency_code"]
        quantity = holding["quantity"]
        if code == base_currency:
            total += quantity
            continue
        rate = rates.get(code)
        if rate is None or rate == 0:
            raise ValueError(f"Missing or invalid rate for {code}")
        total += quantity / rate
    return round(total, 2)


def build_quantities_from_weights(
    total_value_in_base: float,
    weights: list[tuple[str, float]],
    rates: dict[str, float],
    base_currency: str,
) -> list[tuple[str, float, float]]:
    rows: list[tuple[str, float, float]] = []
    for currency_code, weight_percent in weights:
        notional_value = total_value_in_base * weight_percent / 100
        if currency_code == base_currency:
            quantity = notional_value
        else:
            rate = rates.get(currency_code)
            if rate is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Unsupported currency for allocation: {currency_code}",
                )
            quantity = notional_value * rate
        rows.append((currency_code, weight_percent, round(quantity, 6)))
    return rows


def fetch_latest_rates(
    frankfurter: FrankfurterClientProtocol,
    base_currency: str,
    currencies: list[str],
) -> tuple[str, dict[str, float]]:
    non_base = sorted({code for code in currencies if code != base_currency})
    if not non_base:
        return "", {}
    payload = frankfurter.fetch_latest(base_currency, non_base)
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
    total_value_in_base: float,
    rows: list[tuple[str, float, float]],
) -> None:
    db.add(
        RebalanceRecord(
            portfolio_id=portfolio.id,
            base_currency=portfolio.base_currency,
            effective_rates_date=rates_date,
            total_value_usd=round(total_value_in_base, 2),
            holdings_json=_snapshot_rows(rows),
        )
    )


def _resolve_base_value(
    currency_code: str, quantity: float, rates: dict[str, float], base_currency: str
) -> float:
    if currency_code == base_currency:
        return round(quantity, 2)
    rate = rates.get(currency_code)
    if rate is None or rate == 0:
        raise ValueError(f"Missing or invalid rate for {currency_code}")
    return round(quantity / rate, 2)


def _build_holding_details(
    rows: list[tuple[str, float, float]],
    total_value_in_base: float,
    rates: dict[str, float],
    base_currency: str,
) -> list[HoldingDetail]:
    details: list[HoldingDetail] = []
    for currency_code, weight_percent, quantity in rows:
        base_value = _resolve_base_value(currency_code, quantity, rates, base_currency)
        actual_weight = (
            0.0
            if total_value_in_base == 0
            else round(base_value / total_value_in_base * 100, 2)
        )
        details.append(
            {
                "currency_code": currency_code,
                "weight_percent": round(weight_percent, 4),
                "weight_actual_percent": actual_weight,
                "quantity": round(quantity, 6),
                "usd_value": base_value,
            }
        )
    return details


def _find_prior_business_day_rates(
    frankfurter: FrankfurterClientProtocol,
    base_currency: str,
    currencies: list[str],
    current_rates_date: str,
) -> tuple[str | None, dict[str, float]]:
    non_base = sorted({code for code in currencies if code != base_currency})
    if not non_base:
        return None, {}

    end_day = date.fromisoformat(current_rates_date)
    start_day = end_day - timedelta(days=10)
    payload = frankfurter.fetch_history(
        base_currency, non_base, start_day.isoformat(), end_day.isoformat()
    )
    rates_by_date = payload.get("rates", {})
    available_dates = sorted(rates_by_date.keys())

    prior_dates = [day for day in available_dates if day < current_rates_date]
    if not prior_dates:
        return None, {}

    prior_date = prior_dates[-1]
    prior_rates = rates_by_date.get(prior_date, {})
    return prior_date, prior_rates


def create_default_portfolio(db: Session, base_currency: str = "USD") -> Portfolio:
    base_currency = base_currency.upper()
    portfolio = Portfolio(
        id=str(uuid.uuid4()),
        base_currency=base_currency,
        initial_cash_usd=10000.0,
        prior_value_usd=10000.0,
        rates_date=None,
    )
    portfolio.holdings = [
        Holding(
            currency_code=base_currency,
            quantity=10000.0,
            weight_percent=100.0,
        )
    ]
    _ensure_rebalance_record(
        db=db,
        portfolio=portfolio,
        rates_date=date.today().isoformat(),
        total_value_in_base=portfolio.initial_cash_usd,
        rows=[(base_currency, 100.0, portfolio.initial_cash_usd)],
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
    rates_date, rates = fetch_latest_rates(frankfurter, portfolio.base_currency, currency_codes)
    quantities = _to_quantities(holdings)
    total_value = compute_portfolio_value_in_base(quantities, rates, portfolio.base_currency)
    rows = [(holding.currency_code, holding.weight_percent, holding.quantity) for holding in holdings]

    prior_rates_date: str | None = None
    prior_total_value = total_value
    if rates_date:
        prior_rates_date, prior_rates = _find_prior_business_day_rates(
            frankfurter, portfolio.base_currency, currency_codes, rates_date
        )
        if prior_rates_date:
            prior_total_value = compute_portfolio_value_in_base(
                quantities, prior_rates, portfolio.base_currency
            )

    daily_pl = round(total_value - prior_total_value, 2)
    holdings_detail = _build_holding_details(rows, total_value, rates, portfolio.base_currency)

    return {
        "id": portfolio.id,
        "base_currency": portfolio.base_currency,
        "initial_cash_usd": portfolio.initial_cash_usd,
        "total_value_usd": total_value,
        "daily_pl_usd": daily_pl,
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
    existing_rates_date, existing_rates = fetch_latest_rates(
        frankfurter, portfolio.base_currency, existing_currency_codes
    )
    current_total = compute_portfolio_value_in_base(
        existing_quantities, existing_rates, portfolio.base_currency
    )

    preview_currency_codes = [code for code, _ in weights]
    _, preview_rates = fetch_latest_rates(frankfurter, portfolio.base_currency, preview_currency_codes)
    preview_rows = build_quantities_from_weights(
        current_total, weights, preview_rates, portfolio.base_currency
    )
    projected_quantities = [{"currency_code": code, "quantity": qty} for code, _, qty in preview_rows]
    projected_total = compute_portfolio_value_in_base(
        projected_quantities, preview_rates, portfolio.base_currency
    )
    projected_details = _build_holding_details(
        preview_rows, projected_total, preview_rates, portfolio.base_currency
    )

    by_currency_current = {
        currency_code: {
            "quantity": quantity,
            "usd_value": _resolve_base_value(
                currency_code, quantity, existing_rates, portfolio.base_currency
            ),
        }
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
        "base_currency": portfolio.base_currency,
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
    _, existing_rates = fetch_latest_rates(
        frankfurter, portfolio.base_currency, existing_currency_codes
    )
    current_total = compute_portfolio_value_in_base(
        existing_quantities, existing_rates, portfolio.base_currency
    )

    preview_currency_codes = [code for code, _ in weights]
    rates_date, rates = fetch_latest_rates(frankfurter, portfolio.base_currency, preview_currency_codes)
    rows = build_quantities_from_weights(current_total, weights, rates, portfolio.base_currency)

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
    current_value = compute_portfolio_value_in_base(quantities, rates, portfolio.base_currency)
    portfolio.prior_value_usd = current_value
    portfolio.rates_date = rates_date or portfolio.rates_date
    _ensure_rebalance_record(
        db=db,
        portfolio=portfolio,
        rates_date=rates_date or date.today().isoformat(),
        total_value_in_base=current_value,
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
            frankfurter,
            portfolio.base_currency,
            [holding.currency_code for holding in portfolio.holdings],
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
        non_base = sorted({code for code, _, _ in rows if code != portfolio.base_currency})

        if segment_start <= end_day and record.effective_rates_date >= start_day.isoformat():
            markers.append(record.effective_rates_date)

        if not non_base:
            points_by_date[segment_start.isoformat()] = round(
                sum(qty for code, _, qty in rows if code == portfolio.base_currency), 2
            )
            continue

        payload = frankfurter.fetch_history(
            portfolio.base_currency, non_base, segment_start.isoformat(), segment_end.isoformat()
        )
        rates_by_date = payload.get("rates", {})
        for day in sorted(rates_by_date.keys()):
            rates = rates_by_date.get(day, {})
            points_by_date[day] = compute_portfolio_value_in_base(
                quantities, rates, portfolio.base_currency
            )

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
            }
        )
        previous_value = value

    return {
        "base_currency": portfolio.base_currency,
        "points": points,
        "rebalance_markers": sorted(set(markers)),
    }


def portfolio_snapshot_response(
    portfolio: Portfolio,
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    current = portfolio_to_response(portfolio, frankfurter)
    return {
        "base_currency": portfolio.base_currency,
        "as_of": current["rates_date"],
        "total_value_usd": current["total_value_usd"],
        "daily_pl_usd": current["daily_pl_usd"],
        "holdings": current["holdings_detail"],
        "disclaimer": "Simulation only. Not investment advice.",
    }


def _infer_transaction_event_type(
    index: int,
    record: RebalanceRecord,
    previous: RebalanceRecord | None,
) -> str:
    if index == 0:
        return "initial"
    if previous is not None and record.base_currency != previous.base_currency:
        return "base_currency_switch"
    return "rebalance"


def _convert_total_to_base(
    total_in_record_base: float,
    record_base: str,
    portfolio_base: str,
    frankfurter: FrankfurterClientProtocol,
    rate_cache: dict[str, dict[str, float]],
) -> float:
    if record_base == portfolio_base:
        return round(total_in_record_base, 2)
    if record_base not in rate_cache:
        _, rates = fetch_latest_rates(frankfurter, portfolio_base, [record_base])
        rate_cache[record_base] = rates
    return compute_portfolio_value_in_base(
        [{"currency_code": record_base, "quantity": total_in_record_base}],
        rate_cache[record_base],
        portfolio_base,
    )


def portfolio_transactions_response(
    portfolio: Portfolio,
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    records = sorted(portfolio.rebalance_records, key=lambda item: item.created_at)
    rate_cache: dict[str, dict[str, float]] = {}
    transactions = []
    for index, record in enumerate(records):
        previous = records[index - 1] if index > 0 else None
        rows = _parse_snapshot_rows(record.holdings_json)
        event_type = _infer_transaction_event_type(index, record, previous)
        if event_type == "base_currency_switch":
            continue
        transactions.append(
            {
                "id": record.id,
                "event_type": event_type,
                "base_currency": portfolio.base_currency,
                "effective_rates_date": record.effective_rates_date,
                "total_value_usd": _convert_total_to_base(
                    record.total_value_usd,
                    record.base_currency,
                    portfolio.base_currency,
                    frankfurter,
                    rate_cache,
                ),
                "holdings": [
                    {
                        "currency_code": code,
                        "weight_percent": weight,
                        "quantity": quantity,
                    }
                    for code, weight, quantity in rows
                ],
                "created_at": record.created_at.isoformat(),
            }
        )

    return {
        "base_currency": portfolio.base_currency,
        "transactions": list(reversed(transactions)),
    }


def switch_portfolio_base_currency(
    db: Session,
    portfolio: Portfolio,
    base_currency: str,
    frankfurter: FrankfurterClientProtocol,
) -> dict:
    next_base = base_currency.upper()
    if next_base == portfolio.base_currency:
        return portfolio_to_response(portfolio, frankfurter)

    holdings = _rows_from_holdings(portfolio.holdings)
    portfolio.base_currency = next_base
    rates_date, rates = fetch_latest_rates(
        frankfurter, next_base, [holding.currency_code for holding in portfolio.holdings]
    )
    quantities = _to_quantities(portfolio.holdings)
    current_value = compute_portfolio_value_in_base(quantities, rates, next_base)
    portfolio.prior_value_usd = current_value
    portfolio.rates_date = rates_date or portfolio.rates_date
    _ensure_rebalance_record(
        db=db,
        portfolio=portfolio,
        rates_date=rates_date or date.today().isoformat(),
        total_value_in_base=current_value,
        rows=holdings,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio_to_response(portfolio, frankfurter)
