"""Configuration — AP policy thresholds."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AP_", env_file=".env", extra="ignore")

    # Extraction provider: "rules" (default, offline deterministic), "openai", "anthropic".
    extractor: str = "rules"
    model: str = "rules-small"

    # Invoices at or below this total auto-approve when the match is clean.
    auto_approve_under: float = 5000.0
    # Allowed unit-price variance vs the PO (fraction).
    price_tolerance: float = 0.05
    # Allowed total rounding slack (absolute currency).
    total_tolerance: float = 0.01


_CACHE: dict[str, Settings] = {}


def get_settings(name: str = "default") -> Settings:
    if name not in _CACHE:
        _CACHE[name] = Settings()
    return _CACHE[name]


def reset_settings(name: str = "default") -> None:
    _CACHE.pop(name, None)
