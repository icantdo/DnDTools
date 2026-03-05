"""JSON file storage utilities."""

import json
import os
from typing import Any


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    os.makedirs("data", exist_ok=True)


def load_json(filepath: str, default: Any = None) -> Any:
    """Load JSON data from a file.

    Args:
        filepath: Path to the JSON file.
        default: Default value if file doesn't exist or is invalid.

    Returns:
        Loaded JSON data or default value.
    """
    if default is None:
        default = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(filepath: str, data: Any) -> None:
    """Save data to a JSON file.

    Args:
        filepath: Path to the JSON file.
        data: Data to save.
    """
    ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
