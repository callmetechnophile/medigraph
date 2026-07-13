"""Health check and database connectivity probe route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from neo4j import AsyncDriver
import structlog

from app.database.connection import get_driver
from app.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(driver: AsyncDriver = Depends(get_driver)):
    """Liveness probe verifying database connectivity."""
    try:
        await driver.verify_connectivity()
        return {
            "status": "healthy",
            "database": "connected",
            "version": get_settings().app_version
        }
    except Exception as e:
        logger.error("health.check.failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: Database unreachable. {str(e)}"
        )
