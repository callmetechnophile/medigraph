"""Unit tests for PatientRepository using mocked database driver."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import pytest

from app.repositories.patient_repository import PatientRepository

@pytest.mark.asyncio
async def test_find_by_clerk_id_not_found(mock_driver):
    # Mocking driver response for no records
    mock_driver.execute_query.return_value = ([], None, None)
    
    repo = PatientRepository(mock_driver)
    res = await repo.find_by_clerk_id("clerk-id-nonexistent")
    
    assert res is None
    mock_driver.execute_query.assert_called_once()


@pytest.mark.asyncio
async def test_find_by_clerk_id_found(mock_driver):
    # Mock returning one node
    mock_node = MagicMock()
    mock_node.items.return_value = [("id", "patient-1"), ("name", "John Doe"), ("clerk_user_id", "clerk-1")]
    
    mock_record = {"n": mock_node}
    mock_driver.execute_query.return_value = ([mock_record], None, None)
    
    repo = PatientRepository(mock_driver)
    res = await repo.find_by_clerk_id("clerk-1")
    
    assert res is not None
    assert res["id"] == "patient-1"
    assert res["name"] == "John Doe"
    assert res["clerk_user_id"] == "clerk-1"
    mock_driver.execute_query.assert_called_once()
