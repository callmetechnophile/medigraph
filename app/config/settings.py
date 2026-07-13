"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings.

    All values are loaded from environment variables or a `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "Healthcare Intelligence Platform"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # ── Neo4j / AuraDB ──────────────────────────────────────────
    neo4j_uri: str = "neo4j+s://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    neo4j_max_connection_pool_size: int = 50
    neo4j_connection_timeout: float = 30.0

    # ── Clerk Authentication ────────────────────────────────────
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""

    # ── Sarvam AI (Voice) ───────────────────────────────────────
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_default_language: str = "hi-IN"
    sarvam_default_speaker: str = "meera"

    # ── Brevo (Notifications) ──────────────────────────────────
    brevo_api_key: str = ""
    brevo_sender_email: str = "noreply@yourdomain.com"
    brevo_sender_name: str = "Health Platform"

    # ── Supabase (Report Storage) ──────────────────────────────
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_bucket: str = "reports"

    # ── Report Generation ──────────────────────────────────────
    report_temp_dir: str = "./tmp/reports"

    # ── Rate Limiting ──────────────────────────────────────────
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
