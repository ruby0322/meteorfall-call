from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.init_db import init_database
from app.main import create_app
from app.services.portfolio import compute_portfolio_value_usd


def make_settings(database_url: str = "sqlite+pysqlite:///:memory:") -> Settings:
    return Settings(
        frankfurter_base_url="https://api.frankfurter.app",
        cache_ttl_seconds=3600,
        rate_limit_requests=100,
        rate_limit_window_seconds=60,
        cors_origins="http://localhost:3000",
        database_url=database_url,
    )


def make_test_app(settings: Settings | None = None):
    resolved = settings or make_settings()
    engine = create_engine(
        resolved.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    init_database(engine)
    mock_client = MagicMock()
    mock_client.fetch_currencies.return_value = {
        "USD": "United States Dollar",
        "EUR": "Euro",
        "JPY": "Japanese Yen",
    }
    mock_client.fetch_latest.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-08-23",
        "rates": {"EUR": 0.88, "JPY": 150.0},
    }
    mock_client.fetch_history.return_value = {
        "amount": 1.0,
        "base": "USD",
        "rates": {
            "2024-08-22": {"EUR": 0.89, "JPY": 149.5},
            "2024-08-23": {"EUR": 0.88, "JPY": 150.0},
        },
    }
    app = create_app(
        settings=resolved,
        frankfurter_client=mock_client,
        session_factory=session_factory,
    )
    return app, mock_client


def test_compute_portfolio_value_usd_reflects_rate_change() -> None:
    holdings = [{"currency_code": "EUR", "quantity": 9010.0}]

    prior_value = compute_portfolio_value_usd(holdings, {"EUR": 0.901})
    current_value = compute_portfolio_value_usd(holdings, {"EUR": 0.880})

    assert prior_value == 10000.0
    assert current_value > prior_value
    assert round(current_value - prior_value, 2) == 238.64


def test_create_portfolio_starts_with_ten_thousand_usd() -> None:
    app, _ = make_test_app()
    client = TestClient(app)

    response = client.post("/v1/portfolio")

    assert response.status_code == 201
    body = response.json()
    assert body["initial_cash_usd"] == 10000.0
    assert body["total_value_usd"] == 10000.0
    assert body["daily_pl_usd"] == 0.0
    assert body["cumulative_pl_usd"] == 0.0
    assert body["holdings"][0]["currency_code"] == "USD"
    assert body["holdings"][0]["weight_percent"] == 100.0


def test_update_holdings_rebalances_with_preview_rates() -> None:
    app, mock_client = make_test_app()
    mock_client.fetch_latest.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-08-23",
        "rates": {"EUR": 0.901, "JPY": 144.9},
    }
    client = TestClient(app)

    created = client.post("/v1/portfolio").json()
    portfolio_id = created["id"]

    response = client.put(
        f"/v1/portfolio/{portfolio_id}/holdings",
        json={
            "holdings": [
                {"currency_code": "USD", "weight_percent": 50.0},
                {"currency_code": "EUR", "weight_percent": 50.0},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["holdings"]) == 2
    assert sum(item["weight_percent"] for item in body["holdings"]) == 100.0
    assert body["total_value_usd"] == 10000.0
    assert body["rates_date"] == "2024-08-23"


def test_daily_pl_uses_prior_business_day_rates() -> None:
    app, mock_client = make_test_app()
    mock_client.fetch_latest.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-08-23",
        "rates": {"EUR": 0.88},
    }
    mock_client.fetch_history.return_value = {
        "amount": 1.0,
        "base": "USD",
        "rates": {
            "2024-08-22": {"EUR": 0.90},
            "2024-08-23": {"EUR": 0.88},
        },
    }
    client = TestClient(app)
    created = client.post("/v1/portfolio").json()
    portfolio_id = created["id"]

    client.put(
        f"/v1/portfolio/{portfolio_id}/holdings",
        json={"holdings": [{"currency_code": "EUR", "weight_percent": 100.0}]},
    )
    response = client.get(f"/v1/portfolio/{portfolio_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["prior_rates_date"] == "2024-08-22"
    assert body["daily_pl_usd"] == round((8800 / 0.88) - (8800 / 0.9), 2)


def test_rebalance_allocates_current_mtm_not_initial_cash() -> None:
    app, mock_client = make_test_app()
    mock_client.fetch_latest.side_effect = [
        {"amount": 1.0, "base": "USD", "date": "2024-08-23", "rates": {"EUR": 0.90}},
        {"amount": 1.0, "base": "USD", "date": "2024-08-23", "rates": {"EUR": 0.80}},
        {"amount": 1.0, "base": "USD", "date": "2024-08-23", "rates": {"EUR": 0.80}},
        {"amount": 1.0, "base": "USD", "date": "2024-08-23", "rates": {"EUR": 0.80}},
        {"amount": 1.0, "base": "USD", "date": "2024-08-23", "rates": {"EUR": 0.80}},
    ]
    mock_client.fetch_history.return_value = {
        "amount": 1.0,
        "base": "USD",
        "rates": {"2024-08-22": {"EUR": 0.90}, "2024-08-23": {"EUR": 0.80}},
    }
    client = TestClient(app)
    created = client.post("/v1/portfolio").json()
    portfolio_id = created["id"]

    first = client.put(
        f"/v1/portfolio/{portfolio_id}/holdings",
        json={"holdings": [{"currency_code": "EUR", "weight_percent": 100.0}]},
    )
    assert first.status_code == 200

    second = client.put(
        f"/v1/portfolio/{portfolio_id}/holdings",
        json={
            "holdings": [
                {"currency_code": "USD", "weight_percent": 50.0},
                {"currency_code": "EUR", "weight_percent": 50.0},
            ]
        },
    )
    assert second.status_code == 200
    body = second.json()
    assert body["total_value_usd"] == 11250.0
    eur_holding = next(item for item in body["holdings"] if item["currency_code"] == "EUR")
    assert eur_holding["quantity"] == 4500.0


def test_preview_does_not_persist() -> None:
    app, mock_client = make_test_app()
    mock_client.fetch_latest.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-08-23",
        "rates": {"EUR": 0.90},
    }
    client = TestClient(app)
    created = client.post("/v1/portfolio").json()
    portfolio_id = created["id"]

    preview = client.post(
        f"/v1/portfolio/{portfolio_id}/holdings/preview",
        json={
            "holdings": [
                {"currency_code": "USD", "weight_percent": 50.0},
                {"currency_code": "EUR", "weight_percent": 50.0},
            ]
        },
    )
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["total_value_usd"] == 10000.0
    assert len(preview_body["projected_holdings"]) == 2

    current = client.get(f"/v1/portfolio/{portfolio_id}")
    assert current.status_code == 200
    assert current.json()["holdings"][0]["currency_code"] == "USD"
    assert current.json()["holdings"][0]["weight_percent"] == 100.0
