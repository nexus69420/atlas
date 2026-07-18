"""FastAPI application entrypoint.

Architecture (V1 modular monolith):
  Browser → Next.js → FastAPI → Services → Repositories → PostgreSQL

This file wires the app only. Business logic stays in services;
DB access stays in repositories; routes stay thin.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.v1.routes import health
from app.core.config import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    """Application factory — easier to test than a module-level singleton."""
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Unversioned: probes and load balancers expect a stable path
    application.include_router(health.router)

    # Versioned product API
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    return application


app = create_app()
