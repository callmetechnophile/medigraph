"""Neo4j / AuraDB async driver lifecycle and FastAPI dependency injection."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import get_settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Global driver reference (set during lifespan)
# ---------------------------------------------------------------------------
_neo4j_driver: AsyncDriver | None = None


def get_neo4j_driver() -> AsyncDriver:
    """Return the global Neo4j driver. Raises if not initialised."""
    if _neo4j_driver is None:
        raise RuntimeError("Neo4j driver has not been initialised.")
    return _neo4j_driver


# ---------------------------------------------------------------------------
# FastAPI Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def neo4j_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage Neo4j driver startup and shutdown within the FastAPI lifespan."""
    global _neo4j_driver

    settings = get_settings()

    logger.info(
        "neo4j.connecting",
        uri=settings.neo4j_uri,
        database=settings.neo4j_database,
    )

    _neo4j_driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        max_connection_pool_size=settings.neo4j_max_connection_pool_size,
        connection_timeout=settings.neo4j_connection_timeout,
        max_connection_lifetime=3300.0,
        keep_alive=True,
    )

    # Verify connectivity at startup — make it non-fatal to allow boot debugging
    try:
        await _neo4j_driver.verify_connectivity()
        logger.info("neo4j.connected")
    except Exception as exc:
        logger.error("neo4j.connection_failed_on_startup", error=str(exc))

    # Store on app.state for direct access in middleware if needed
    app.state.neo4j_driver = _neo4j_driver

    yield

    # Shutdown
    logger.info("neo4j.closing")
    await _neo4j_driver.close()
    _neo4j_driver = None
    logger.info("neo4j.closed")


# ---------------------------------------------------------------------------
# FastAPI Dependency — inject driver into routes / services
# ---------------------------------------------------------------------------
def get_driver(request: Request) -> AsyncDriver:
    """FastAPI dependency that returns the Neo4j async driver from app state."""
    driver: AsyncDriver = request.app.state.neo4j_driver
    if driver is None:
        raise RuntimeError("Neo4j driver is not available.")
    return driver
