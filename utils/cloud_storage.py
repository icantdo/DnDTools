"""Storage abstraction layer for future cloud sync support.

Currently only LocalBackend is implemented, wrapping the existing JSON file storage.
To add cloud support, implement the StorageBackend ABC and register it in get_storage_backend().
"""

from abc import ABC, abstractmethod
from typing import Any

from config import SAVED_ENCOUNTERS_FILE, SAVED_ITEMS_FILE
from .storage import load_json, save_json


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def load_encounters(self) -> list[dict]:
        """Load all saved encounters."""

    @abstractmethod
    def save_encounter(self, encounter: dict) -> bool:
        """Save or update an encounter. Returns True on success."""

    @abstractmethod
    def load_items(self) -> list[dict]:
        """Load all saved magic items."""

    @abstractmethod
    def save_item(self, item: dict) -> bool:
        """Save a magic item. Returns True on success."""


class LocalBackend(StorageBackend):
    """Local JSON file storage — the default backend."""

    def load_encounters(self) -> list[dict]:
        return load_json(SAVED_ENCOUNTERS_FILE, [])

    def save_encounter(self, encounter: dict) -> bool:
        try:
            encounters = self.load_encounters()
            existing = next(
                (i for i, e in enumerate(encounters) if e.get("name") == encounter.get("name")),
                None,
            )
            if existing is not None:
                encounters[existing] = encounter
            else:
                encounters.append(encounter)
            save_json(SAVED_ENCOUNTERS_FILE, encounters)
            return True
        except Exception:
            return False

    def load_items(self) -> list[dict]:
        return load_json(SAVED_ITEMS_FILE, [])

    def save_item(self, item: dict) -> bool:
        try:
            items = self.load_items()
            items.append(item)
            save_json(SAVED_ITEMS_FILE, items)
            return True
        except Exception:
            return False


class NullCloudBackend(StorageBackend):
    """Placeholder no-op backend. Replace with a real cloud implementation later."""

    def load_encounters(self) -> list[dict]:
        return []

    def save_encounter(self, encounter: dict) -> bool:
        return False

    def load_items(self) -> list[dict]:
        return []

    def save_item(self, item: dict) -> bool:
        return False


def get_storage_backend() -> StorageBackend:
    """Return the active storage backend.

    Reads from session state if available. Defaults to LocalBackend.
    When a cloud backend is implemented, set st.session_state.storage_backend = 'cloud'
    and add the corresponding branch here.
    """
    try:
        import streamlit as st
        backend_name = st.session_state.get("storage_backend", "local")
    except Exception:
        backend_name = "local"

    if backend_name == "local":
        return LocalBackend()

    # Future cloud backends can be registered here:
    # if backend_name == "supabase":
    #     return SupabaseBackend(...)

    return LocalBackend()
