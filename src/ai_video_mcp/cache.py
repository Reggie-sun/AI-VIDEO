from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    timestamp: float


class AnalysisCache:
    def __init__(self, max_size: int = 32, ttl_seconds: int = 3600):
        self._cache: OrderedDict[tuple, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds

    def _make_key(self, path: str | Path, operation: str, **kwargs: Any) -> tuple:
        stat = Path(path).stat()
        extra = tuple(sorted(kwargs.items())) if kwargs else ()
        return (str(path), stat.st_mtime, stat.st_size, operation, extra)

    def get(self, path: str | Path, operation: str, **kwargs: Any) -> Any | None:
        key = self._make_key(path, operation, **kwargs)
        entry = self._cache.get(key)
        if entry and (time.time() - entry.timestamp) < self._ttl:
            self._cache.move_to_end(key)
            return entry.value
        if key in self._cache:
            del self._cache[key]
        return None

    def set(self, path: str | Path, operation: str, value: Any, **kwargs: Any) -> None:
        key = self._make_key(path, operation, **kwargs)
        self._cache[key] = CacheEntry(value=value, timestamp=time.time())
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()
