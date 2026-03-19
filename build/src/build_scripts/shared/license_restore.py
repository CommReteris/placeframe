from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic_settings import BaseSettings

from .cache import restore


def license_cache_tag() -> str:
    return f"v-{datetime.now(UTC).strftime('%Y-%m-%d')}"


class Settings(BaseSettings):
    cache_registry: str


settings = Settings.model_validate({})


def restore_license() -> None:
    license_directory = Path.home() / ".local" / "share" / "unity3d" / "Unity"
    license_directory.mkdir(parents=True, exist_ok=True)
    restore(settings.cache_registry, "unity-license", license_cache_tag(), license_directory, required=True)
