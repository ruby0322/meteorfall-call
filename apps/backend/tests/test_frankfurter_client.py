import httpx
import pytest

from app.services.frankfurter import FrankfurterClient


def test_frankfurter_client_enables_redirect_following() -> None:
    client = FrankfurterClient("https://api.frankfurter.app")
    try:
        assert client._client.follow_redirects is True
    finally:
        client.close()


def test_fetch_currencies_follows_frankfurter_app_redirect() -> None:
    """Regression: legacy .app host 301s to api.frankfurter.dev/v1."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.frankfurter.app":
            return httpx.Response(
                301,
                headers={"Location": "https://api.frankfurter.dev/v1/currencies"},
            )
        return httpx.Response(
            200,
            json={"USD": "United States Dollar", "EUR": "Euro"},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, follow_redirects=True)
    client = FrankfurterClient("https://api.frankfurter.app", http_client=http_client)
    try:
        currencies = client.fetch_currencies()
        assert currencies["EUR"] == "Euro"
    finally:
        client.close()
        http_client.close()


def test_fetch_currencies_fails_when_redirects_disabled() -> None:
    """Documents the original production failure mode."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            301,
            headers={"Location": "https://api.frankfurter.dev/v1/currencies"},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, follow_redirects=False)
    client = FrankfurterClient("https://api.frankfurter.app", http_client=http_client)
    try:
        with pytest.raises(httpx.HTTPStatusError, match="301"):
            client.fetch_currencies()
    finally:
        client.close()
        http_client.close()


def test_fetch_latest_uses_canonical_dev_base_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.frankfurter.dev"
        assert request.url.path == "/v1/latest"
        return httpx.Response(
            200,
            json={
                "amount": 1.0,
                "base": "USD",
                "date": "2026-05-22",
                "rates": {"EUR": 0.86244, "JPY": 159.15},
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, follow_redirects=True)
    client = FrankfurterClient("https://api.frankfurter.dev/v1", http_client=http_client)
    try:
        payload = client.fetch_latest("USD", ["EUR", "JPY"])
        assert payload["rates"]["EUR"] == 0.86244
    finally:
        client.close()
        http_client.close()
