from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.services.cache import MemoryCache
from app.services.frankfurter import FrankfurterClient, FrankfurterClientProtocol
from app.services.rate_limit import RateLimiter


def create_app(
    settings: Settings | None = None,
    frankfurter_client: FrankfurterClientProtocol | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    cache = MemoryCache()
    frankfurter = frankfurter_client or FrankfurterClient(resolved_settings.frankfurter_base_url)
    rate_limiter = RateLimiter(
        max_requests=resolved_settings.rate_limit_requests,
        window_seconds=resolved_settings.rate_limit_window_seconds,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if isinstance(app.state.frankfurter, FrankfurterClient):
            app.state.frankfurter.close()

    app = FastAPI(title=resolved_settings.app_name, lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.cache = cache
    app.state.frankfurter = frankfurter
    app.state.rate_limiter = rate_limiter

    origins = [
        origin.strip()
        for origin in resolved_settings.cors_origins.split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
