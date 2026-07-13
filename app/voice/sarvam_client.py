"""Sarvam AI API client wrapper for speech recognition and generation."""

from __future__ import annotations

import base64
import httpx
import structlog

logger = structlog.get_logger(__name__)

class SarvamClient:
    def __init__(self, api_key: str, base_url: str = "https://api.sarvam.ai"):
        self.api_key = api_key
        self.base_url = base_url

    async def speech_to_text(self, audio_bytes: bytes, language_code: str = "hi-IN", model: str = "saaras:v3") -> str:
        """Transcribe short audio using Sarvam API."""
        if not self.api_key:
            logger.warning("sarvam.api_key_missing")
            return ""

        url = f"{self.base_url}/speech-to-text"
        headers = {"api-subscription-key": self.api_key}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {
            "model": model,
            "language_code": language_code,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, data=data, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return result.get("transcript", "")

    async def text_to_speech(self, text: str, target_language_code: str = "hi-IN", speaker: str = "meera", model: str = "bulbul:v3") -> bytes:
        """Generate speech WAV bytes from input text."""
        if not self.api_key:
            logger.warning("sarvam.api_key_missing")
            return b""

        url = f"{self.base_url}/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "target_language_code": target_language_code,
            "model": model,
            "speaker": speaker,
            "pace": 1.0,
            "output_audio_codec": "wav"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            audio_base64 = result["audios"][0]
            return base64.b64decode(audio_base64)
