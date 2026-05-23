from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

LATEST_RESPONSE = {
    "amount": 1.0,
    "base": "USD",
    "date": "2024-08-23",
    "rates": {"EUR": 0.901, "JPY": 144.9},
}

CURRENCIES_RESPONSE = {
    "USD": "United States Dollar",
    "EUR": "Euro",
    "JPY": "Japanese Yen",
}


def make_settings() -> Settings:
    return Settings(
        frankfurter_base_url="https://api.frankfurter.app",
        cache_ttl_seconds=3600,
        rate_limit_requests=100,
        rate_limit_window_seconds=60,
        cors_origins="http://localhost:3000",
    )


def test_latest_rates_uses_cache_on_second_request() -> None:
    mock_client = MagicMock()
    mock_client.fetch_latest.return_value = LATEST_RESPONSE
    mock_client.fetch_currencies.return_value = CURRENCIES_RESPONSE

    app = create_app(settings=make_settings(), frankfurter_client=mock_client)
    client = TestClient(app)

    first = client.get("/v1/rates/latest", params={"base": "USD", "symbols": "EUR,JPY"})
    second = client.get("/v1/rates/latest", params={"base": "USD", "symbols": "EUR,JPY"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["rates"]["EUR"] == 0.901
    assert mock_client.fetch_latest.call_count == 1
    assert second.headers.get("X-Cache-Status") == "HIT"


def test_twd_in_symbols_returns_422_without_upstream_call() -> None:
    mock_client = MagicMock()
    mock_client.fetch_currencies.return_value = CURRENCIES_RESPONSE

    app = create_app(settings=make_settings(), frankfurter_client=mock_client)
    client = TestClient(app)

    response = client.get("/v1/rates/latest", params={"base": "USD", "symbols": "EUR,TWD"})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "TWD" in detail["unsupported"]
    mock_client.fetch_latest.assert_not_called()
