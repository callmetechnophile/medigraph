"""Pytest fixtures for testing FastAPI and repositories with mocked databases."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.connection import get_driver

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_driver():
    """Create a fully mocked Neo4j AsyncDriver."""
    driver = MagicMock()
    # Mock execute_query
    driver.execute_query = AsyncMock(return_value=([], None, None))
    # Mock verify_connectivity
    driver.verify_connectivity = AsyncMock()
    return driver

@pytest.fixture
def test_client(mock_driver) -> TestClient:
    """FastAPI TestClient overriding database dependencies."""
    fastapi_app.dependency_overrides[get_driver] = lambda: mock_driver
    with TestClient(fastapi_app) as client:
        yield client
    fastapi_app.dependency_overrides.clear()
