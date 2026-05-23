from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.core.config import Settings
from app.services.cache import MemoryCache
from app.services.frankfurter import FrankfurterClientProtocol
from app.services.rate_limit import RateLimiter, client_ip

router = APIRouter(prefix="/v1", tags=["rates"])

KNOWN_UNSUPPORTED = {"TWD"}


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_cache(request: Request) -> MemoryCache:
    return request.app.state.cache


def get_frankfurter(request: Request) -> FrankfurterClientProtocol:
    return request.app.state.frankfurter


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def parse_symbols(raw: str) -> list[str]:
    return [symbol.strip().upper() for symbol in raw.split(",") if symbol.strip()]


def validate_symbols(
    symbols: list[str],
    supported: dict[str, str],
) -> None:
    unsupported = sorted(
        symbol
        for symbol in symbols
        if symbol in KNOWN_UNSUPPORTED or symbol not in supported
    )
    if not unsupported:
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "unsupported": unsupported,
            "message": (
                "One or more currency codes are not available from Frankfurter "
                "ECB reference rates."
            ),
            "supported_currencies_url": "/v1/currencies",
        },
    )


@router.get("/currencies")
def list_currencies(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[MemoryCache, Depends(get_cache)],
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> dict[str, str]:
    rate_limiter.check(client_ip(request))
    cache_key = "currencies"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    currencies = frankfurter.fetch_currencies()
    cache.set(cache_key, currencies, settings.cache_ttl_seconds)
    return currencies


@router.get("/rates/latest")
def latest_rates(
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[MemoryCache, Depends(get_cache)],
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    base: Annotated[str, Query(min_length=3, max_length=3)] = "USD",
    symbols: Annotated[str, Query(min_length=3)] = "EUR,JPY,GBP,CNY,SGD",
) -> dict:
    rate_limiter.check(client_ip(request))
    base_code = base.upper()
    symbol_list = parse_symbols(symbols)
    supported = frankfurter.fetch_currencies()
    validate_symbols(symbol_list, supported)

    cache_key = f"latest:{base_code}:{','.join(symbol_list)}"
    cached = cache.get(cache_key)
    if cached is not None:
        response.headers["X-Cache-Status"] = "HIT"
        return cached

    payload = frankfurter.fetch_latest(base_code, symbol_list)
    cache.set(cache_key, payload, settings.cache_ttl_seconds)
    response.headers["X-Cache-Status"] = "MISS"
    return payload


@router.get("/rates/history")
def history_rates(
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    cache: Annotated[MemoryCache, Depends(get_cache)],
    frankfurter: Annotated[FrankfurterClientProtocol, Depends(get_frankfurter)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    start: Annotated[str, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")],
    end: Annotated[str, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")],
    base: Annotated[str, Query(min_length=3, max_length=3)] = "USD",
    symbols: Annotated[str, Query(min_length=3)] = "EUR",
) -> dict:
    rate_limiter.check(client_ip(request))
    base_code = base.upper()
    symbol_list = parse_symbols(symbols)
    supported = frankfurter.fetch_currencies()
    validate_symbols(symbol_list, supported)

    cache_key = f"history:{base_code}:{','.join(symbol_list)}:{start}:{end}"
    cached = cache.get(cache_key)
    if cached is not None:
        response.headers["X-Cache-Status"] = "HIT"
        return cached

    payload = frankfurter.fetch_history(base_code, symbol_list, start, end)
    cache.set(cache_key, payload, settings.cache_ttl_seconds)
    response.headers["X-Cache-Status"] = "MISS"
    return payload
