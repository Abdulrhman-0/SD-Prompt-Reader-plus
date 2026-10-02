__author__ = "receyuki"
__filename__ = "config.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

"""Tiny dependency-free JSON settings store.

Used to remember things like the last opened folder so they survive a restart.
Every operation is defensive: a missing, unreadable or corrupt config file must
never prevent the application from starting.
"""

import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "SDPromptReader"
CONFIG_FILE_NAME = "config.json"


def config_directory() -> Path:
    """Return the per-user directory used to store settings."""
    override = os.environ.get("SD_PROMPT_READER_CONFIG_DIR")
    if override:
        return Path(override)

    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    else:
        base = os.environ.get("XDG_CONFIG_HOME")
        if base:
            return Path(base) / APP_DIR_NAME
    return Path.home() / ".config" / APP_DIR_NAME


class Config:
    """A minimal key/value store persisted as a single JSON file."""

    def __init__(self, path: Path = None):
        self._path = Path(path) if path else config_directory() / CONFIG_FILE_NAME
        self._data = {}
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    def load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._data = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            self._data = {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def update(self, values: dict):
        if not values:
            return
        self._data.update(values)
        self.save()

    def save(self):
        """Write atomically; silently ignore failures (read-only home, etc.)."""
        temp_path = self._path.with_suffix(".tmp")
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self._path)
        except OSError:
            try:
                temp_path.unlink()
            except OSError:
                pass
