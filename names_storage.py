from __future__ import annotations

import json
from pathlib import Path
from typing import List


class NameStore:
    """Simple storage for a list of names saved as JSON.

    Responsibilities:
    - Encapsulate file read/write for names.
    - Keep API separate from any CLI code.
    """

    def __init__(self, file_path: str | Path = "data/names.json") -> None:
        self.path = Path(file_path)
        # Ensure parent exists
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if missing
        if not self.path.exists():
            self._write_names([])

    def _read_names(self) -> List[str]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            return [str(x) for x in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_names(self, names: List[str]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(names, f, ensure_ascii=False, indent=2)

    def add_name(self, name: str) -> None:
        """Add a name to storage. Duplicate names are allowed (preserve order)."""
        names = self._read_names()
        names.append(name)
        self._write_names(names)

    def list_names(self) -> List[str]:
        """Return the stored names as a list in insertion order."""
        return self._read_names()


__all__ = ["NameStore"]
