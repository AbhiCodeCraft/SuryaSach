from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from time import monotonic
from typing import Protocol

from app.schemas.solar_resource import SolarWeatherDay


class SolarResourceCache(Protocol):
    def get(self, key: str) -> SolarWeatherDay | None: ...

    def put(self, key: str, value: SolarWeatherDay, ttl_seconds: float) -> None: ...


class MemorySolarResourceCache:
    """Bounded process-local LRU cache; expiration uses a monotonic clock."""

    def __init__(self, max_entries: int = 512, clock: Callable[[], float] = monotonic):
        if max_entries < 1:
            raise ValueError("Cache capacity must be positive")
        self._max_entries = max_entries
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, SolarWeatherDay]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> SolarWeatherDay | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires, value = entry
            if expires <= self._clock():
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return value

    def put(self, key: str, value: SolarWeatherDay, ttl_seconds: float) -> None:
        with self._lock:
            self._entries[key] = (self._clock() + ttl_seconds, value)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
