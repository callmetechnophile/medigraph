"""Voice service — Speech recognition, parsing and voice output."""

from __future__ import annotations

import base64
from typing import Any
from fastapi import HTTPException
import structlog
import httpx

from app.schemas import VoiceCommandResponse, TTSResponse
from app.voice.intent_parser import IntentParser
from app.repositories import InventoryRepository

logger = structlog.get_logger(__name__)

class VoiceService:
    def __init__(
        self,
        inventory_repo: InventoryRepository,
        sarvam_api_key: str,
        sarvam_base_url: str,
        stt_model: str,
        tts_model: str,
        default_language: str = "hi-IN",
        default_speaker: str = "meera",
    ):
        self.inventory_repo = inventory_repo
        self.sarvam_api_key = sarvam_api_key
        self.sarvam_base_url = sarvam_base_url
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.default_language = default_language
        self.default_speaker = default_speaker
        self.intent_parser = IntentParser()

    async def speech_to_text(self, audio_bytes: bytes, language_code: str) -> str:
        if not self.sarvam_api_key:
            logger.warning("sarvam.api_key_missing")
            # fallback mock transcript
            return "update Paracetamol stock to 120"

        url = f"{self.sarvam_base_url}/speech-to-text"
        headers = {"api-subscription-key": self.sarvam_api_key}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {
            "model": self.stt_model,
            "language_code": language_code or self.default_language,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                return result.get("transcript", "")
            except Exception as e:
                logger.error("sarvam.stt_failed", error=str(e))
                raise HTTPException(status_code=502, detail=f"Sarvam STT failed: {str(e)}")

    async def text_to_speech(self, text: str, language_code: str, speaker: str) -> bytes:
        if not self.sarvam_api_key:
            logger.warning("sarvam.api_key_missing")
            # mock empty bytes
            return b"mock_audio_data"

        url = f"{self.sarvam_base_url}/text-to-speech"
        headers = {
            "api-subscription-key": self.sarvam_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "target_language_code": language_code or self.default_language,
            "model": self.tts_model,
            "speaker": speaker or self.default_speaker,
            "pace": 1.0,
            "output_audio_codec": "wav"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                # Audio is returned as base64-encoded WAV
                audio_base64 = result["audios"][0]
                return base64.b64decode(audio_base64)
            except Exception as e:
                logger.error("sarvam.tts_failed", error=str(e))
                raise HTTPException(status_code=502, detail=f"Sarvam TTS failed: {str(e)}")

    async def process_voice_command(self, audio_bytes: bytes, language_code: str, hospital_id: str) -> VoiceCommandResponse:
        # 1. Speech-to-Text
        transcript = await self.speech_to_text(audio_bytes, language_code)
        
        # 2. Intent Extraction
        parsed = self.intent_parser.parse(transcript)
        intent = parsed["intent"]
        entities = parsed["entities"]
        
        # 3. Route & Validate
        action_result = {}
        response_text = "Command not recognized."
        success = False

        if intent == "update_stock":
            medicine = entities.get("medicine")
            quantity = entities.get("quantity")
            if medicine and quantity is not None:
                inv_items = await self.inventory_repo.find_by_medicine_name(hospital_id, medicine)
                if inv_items:
                    target_id = inv_items[0]["id"]
                    updated = await self.inventory_repo.update_stock(target_id, quantity)
                    action_result = {"updated_item": updated}
                    response_text = f"Updated stock for {medicine} to {quantity} units."
                    success = True
                else:
                    response_text = f"Could not find medicine {medicine} in hospital inventory."
            else:
                response_text = "Failed to parse medicine name or quantity from command."

        elif intent == "check_stock":
            medicine = entities.get("medicine")
            if medicine:
                inv_items = await self.inventory_repo.find_by_medicine_name(hospital_id, medicine)
                if inv_items:
                    current_stock = inv_items[0]["current_stock"]
                    action_result = {"current_stock": current_stock}
                    response_text = f"Current stock of {medicine} is {current_stock} units."
                    success = True
                else:
                    response_text = f"Medicine {medicine} not found in inventory."
            else:
                response_text = "Failed to identify medicine name."

        # 4. Text-to-Speech response
        response_audio_base64 = ""
        try:
            audio_data = await self.text_to_speech(response_text, language_code, self.default_speaker)
            response_audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        except Exception:
            pass

        return VoiceCommandResponse(
            transcript=transcript,
            intent=intent,
            entities=entities,
            action_result=action_result,
            response_text=response_text,
            response_audio_base64=response_audio_base64,
            success=success,
        )
