from __future__ import annotations

from pathlib import Path
import json
import tempfile
from threading import RLock
from typing import Any, Callable

from app.core.config import settings


_locks: dict[Path, RLock] = {}
_locks_guard = RLock()


def _lock_for(path: Path) -> RLock:
    resolved = path.resolve()
    with _locks_guard:
        if resolved not in _locks:
            _locks[resolved] = RLock()
        return _locks[resolved]


class JsonStore:
    def __init__(self, name: str) -> None:
        self.path = settings.state_dir / f"{name}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = _lock_for(self.path)

    def read(self, default: Any) -> Any:
        with self._lock:
            if not self.path.exists():
                return default
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    def update(self, default: Any, mutator: Callable[[Any], Any]) -> Any:
        with self._lock:
            payload = self.read(default)
            result = mutator(payload)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent) as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                temp_name = handle.name
            Path(temp_name).replace(self.path)
            return result


def store(name: str) -> JsonStore:
    return JsonStore(name)