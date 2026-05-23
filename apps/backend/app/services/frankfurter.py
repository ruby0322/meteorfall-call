from typing import Protocol

import httpx


class FrankfurterClientProtocol(Protocol):
    def fetch_latest(self, base: str, symbols: list[str]) -> dict:
        ...

    def fetch_history(
        self,
        base: str,
        symbols: list[str],
        start: str,
        end: str,
    ) -> dict:
        ...

    def fetch_currencies(self) -> dict[str, str]:
        ...


class FrankfurterClient:
    def __init__(self, base_url: str, http_client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(timeout=10.0, follow_redirects=True)
        self._owns_client = http_client is None

    def fetch_latest(self, base: str, symbols: list[str]) -> dict:
        params = {"from": base, "to": ",".join(symbols)}
        response = self._client.get(f"{self.base_url}/latest", params=params)
        response.raise_for_status()
        return response.json()

    def fetch_history(
        self,
        base: str,
        symbols: list[str],
        start: str,
        end: str,
    ) -> dict:
        params = {"from": base, "to": ",".join(symbols)}
        response = self._client.get(
            f"{self.base_url}/{start}..{end}",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def fetch_currencies(self) -> dict[str, str]:
        response = self._client.get(f"{self.base_url}/currencies")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
