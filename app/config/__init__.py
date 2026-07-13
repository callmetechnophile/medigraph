"""Configuration package — singleton settings instance."""

from functools import lru_cache

from app.config.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
