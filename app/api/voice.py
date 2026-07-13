"""Voice endpoints — Speech recognition and voice command routing."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import InventoryRepository
from app.services import VoiceService
from app.schemas import VoiceCommandResponse, TTSRequest, TTSResponse
from app.auth.dependencies import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/voice", tags=["Voice"])

def get_voice_service(driver: AsyncDriver = Depends(get_driver)) -> VoiceService:
    repo = InventoryRepository(driver)
    settings = get_settings()
    return VoiceService(
        repo,
        sarvam_api_key=settings.sarvam_api_key,
        sarvam_base_url=settings.sarvam_base_url,
        stt_model=settings.sarvam_stt_model,
        tts_model=settings.sarvam_tts_model,
        default_language=settings.sarvam_default_language,
        default_speaker=settings.sarvam_default_speaker
    )

@router.post("/speech-to-text")
async def speech_to_text(
    file: UploadFile = File(...),
    language_code: str = Form("hi-IN"),
    service: VoiceService = Depends(get_voice_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Transcribe audio files into text transcripts."""
    audio_bytes = await file.read()
    transcript = await service.speech_to_text(audio_bytes, language_code)
    return {"transcript": transcript}

@router.post("/text-to-speech", response_model=TTSResponse)
async def text_to_speech(
    data: TTSRequest,
    service: VoiceService = Depends(get_voice_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Synthesize voice audio from input text."""
    import base64
    audio_data = await service.text_to_speech(data.text, data.language_code, data.speaker)
    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
    return TTSResponse(audio_base64=audio_base64, language_code=data.language_code)

@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    file: UploadFile = File(...),
    language_code: str = Form("hi-IN"),
    hospital_id: str = Form(...),
    service: VoiceService = Depends(get_voice_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Process a voice command. (Upload audio -> Transcribe -> Extract Intent -> Action -> TTS Response)."""
    audio_bytes = await file.read()
    return await service.process_voice_command(audio_bytes, language_code, hospital_id)
