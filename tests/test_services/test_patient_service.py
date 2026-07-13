"""Unit tests for PatientService orchestrations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException

from app.services.patient_service import PatientService
from app.schemas import PatientCreate

@pytest.mark.asyncio
async def test_register_patient_already_exists():
    mock_repo = MagicMock()
    # Mocking patient_repo.find_by_clerk_id to return pre-existing patient
    mock_repo.find_by_clerk_id = AsyncMock(return_value={"id": "pat-123"})
    
    service = PatientService(mock_repo)
    data = PatientCreate(name="John Doe", phone="+919999999999", email="john@example.com")
    
    with pytest.raises(HTTPException) as exc_info:
        await service.register_patient("clerk-id-exists", data)
        
    assert exc_info.value.status_code == 400
    assert "already registered" in exc_info.value.detail


@pytest.mark.asyncio
async def test_register_patient_success():
    mock_repo = MagicMock()
    mock_repo.find_by_clerk_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value={
        "id": "pat-new", "name": "John Doe", "clerk_user_id": "clerk-new",
        "gender": "other", "allergies": [], "chronic_conditions": []
    })
    
    service = PatientService(mock_repo)
    data = PatientCreate(name="John Doe")
    res = await service.register_patient("clerk-new", data)
    
    assert res.id == "pat-new"
    assert res.name == "John Doe"
    assert res.clerk_user_id == "clerk-new"
