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
