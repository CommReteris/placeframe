from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

from .cache import restore


class Settings(BaseSettings):
    cache_registry: str


settings = Settings.model_validate({})


def restore_license() -> None:
    license_directory = Path.home() / ".local" / "share" / "unity3d" / "Unity"
    license_directory.mkdir(parents=True, exist_ok=True)
    restore(settings.cache_registry, "unity-license", "v1", license_directory, required=True)
