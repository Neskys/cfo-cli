"""User configuration stored in ~/.cfo/config.json (not the database)."""

import json
from pathlib import Path

DEFAULTS = {"base_currency": "EUR"}


def _config_path() -> Path:
    config_dir = Path.home() / ".cfo"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict:
    path = _config_path()
    if path.exists():
        try:
            return {**DEFAULTS, **json.loads(path.read_text())}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def get_base_currency() -> str:
    return load_config()["base_currency"]


def set_base_currency(currency: str) -> str:
    config = load_config()
    config["base_currency"] = currency.upper()
    _config_path().write_text(json.dumps(config, indent=2))
    return config["base_currency"]


DEFAULT_PROVIDER = "anthropic"


def _save(config: dict) -> None:
    _config_path().write_text(json.dumps(config, indent=2))


def get_provider() -> str:
    return load_config().get("ai_provider", DEFAULT_PROVIDER)


def set_provider(provider: str) -> None:
    config = load_config()
    config["ai_provider"] = provider
    _save(config)


def get_api_key(provider: str | None = None) -> str | None:
    provider = provider or get_provider()
    return load_config().get(f"{provider}_api_key")


def set_api_key(api_key: str, provider: str | None = None) -> None:
    provider = provider or get_provider()
    config = load_config()
    config[f"{provider}_api_key"] = api_key
    _save(config)


def get_ai_model(provider: str | None = None) -> str | None:
    """Per-provider model override, or None to use the provider's default."""
    provider = provider or get_provider()
    return load_config().get(f"{provider}_model")


def set_ai_model(model: str, provider: str | None = None) -> None:
    provider = provider or get_provider()
    config = load_config()
    config[f"{provider}_model"] = model
    _save(config)


def get_base_url(provider: str | None = None) -> str | None:
    """Per-provider base-URL override (for OpenAI-compatible servers like Ollama)."""
    provider = provider or get_provider()
    return load_config().get(f"{provider}_base_url")


def set_base_url(base_url: str, provider: str | None = None) -> None:
    provider = provider or get_provider()
    config = load_config()
    config[f"{provider}_base_url"] = base_url
    _save(config)
