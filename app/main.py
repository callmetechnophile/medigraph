"""Healthcare Intelligence Platform — FastAPI Application Entry Point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.connection import neo4j_lifespan
from app.database.init_db import init_database
from app.middleware import AuditMiddleware, LoggingMiddleware, register_exception_handlers

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Structured logging configuration
# ---------------------------------------------------------------------------
def _configure_logging() -> None:
    """Configure structlog with JSON or console output based on environment."""
    settings = get_settings()
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.is_production:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle — startup and shutdown."""
    _configure_logging()
    logger.info("app.starting", version=get_settings().app_version)

    # Start Neo4j driver
    async with neo4j_lifespan(app):
        # Initialise database schema (constraints + indexes)
        driver = app.state.neo4j_driver
        try:
            await init_database(driver, get_settings().neo4j_database)
        except Exception as exc:
            logger.error("database.init.failed_on_startup", error=str(exc))

        logger.info("app.ready")
        yield

    logger.info("app.shutdown")


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Healthcare Intelligence Platform API",
        description=(
            "Enterprise backend for the Healthcare Intelligence Platform. "
            "Provides APIs for Patient Portal, Hospital Operations Portal, "
            "and District Health Intelligence Portal."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Health", "description": "Health check and service status"},
            {"name": "Patients", "description": "Patient registration, records, prescriptions, diagnoses"},
            {"name": "Hospitals", "description": "Hospital management, departments, doctors"},
            {"name": "Inventory", "description": "Medicine inventory and stock management"},
            {"name": "Attendance", "description": "Staff attendance tracking"},
            {"name": "Diagnostics", "description": "Equipment, lab reports, imaging reports"},
            {"name": "Ambulances", "description": "Ambulance fleet management"},
            {"name": "Reports", "description": "Report generation (PDF, CSV, Excel)"},
            {"name": "Notifications", "description": "In-app notification management"},
            {"name": "Recommendations", "description": "AI-generated recommendations"},
            {"name": "Voice", "description": "Sarvam AI voice commands (STT, TTS)"},
            {"name": "Workflow", "description": "Automated workflow triggers"},
            {"name": "HMI", "description": "Hospital Management Index scores"},
            {"name": "Dashboard", "description": "Aggregated dashboard data"},
        ],
    )

    # -- CORS --
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Custom Middleware (order matters: outermost runs first) --
    app.add_middleware(AuditMiddleware)
    app.add_middleware(LoggingMiddleware)

    # -- Exception Handlers --
    register_exception_handlers(app)

    # -- API Routes --
    # Import here to avoid circular imports
    from app.api import api_router

    app.include_router(api_router)

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn)
# ---------------------------------------------------------------------------
app = create_app()
