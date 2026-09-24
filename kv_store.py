from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from time import time_ns


def wall_clock_ms() -> int:
    """Return the current Unix timestamp in milliseconds."""
    return time_ns() // 1_000_000


class KeyNotFoundError(KeyError):
    """Raised when an operation requires a key that does not exist."""


class KVStore:
    """A key-value store with string keys and optional expiration."""

    def __init__(
        self,
        *,
        clock: Callable[[], int] = wall_clock_ms,
    ) -> None:
        self._data: dict[str, str] = {}
        self._expires_at: OrderedDict[str, int] = OrderedDict()
        self._clock = clock
        self._batch_size = 10
        self._lock = Lock()

    def set(
        self,
        key: str,
        value: str,
        ttl_ms: int | None = None,
    ) -> None:
        """Insert or replace a value and its optional TTL.

        ttl_ms=None removes any previous expiration.
        ttl_ms <= 0 raises ValueError without changing the entry.
        """
        with self._lock:
            if ttl_ms is not None and ttl_ms <= 0:
                raise ValueError(f"ttl_ms {ttl_ms} must be > 0")

            deadline = None if ttl_ms is None else self._clock() + ttl_ms

            if deadline is None:
                self._expires_at.pop(key, None)

            self._data[key] = value

            if deadline is not None:
                self._expires_at[key] = deadline

    def get(self, key: str) -> str:
        """Return the value, or raise KeyNotFoundError if missing or expired."""
        with self._lock:
            self._expire_if_needed(key)

            if key not in self._data:
                raise KeyNotFoundError(key)

            return self._data[key]

    def delete(self, key: str) -> None:
        """Remove the key, or raise KeyNotFoundError if missing or expired."""
        with self._lock:
            self._expire_if_needed(key)

            if key not in self._data:
                raise KeyNotFoundError(key)

            del self._data[key]
            self._expires_at.pop(key, None)

    def _expire_if_needed(self, key: str) -> None:
        """Remove an expired key. Caller must hold self._lock."""
        if (
            key in self._expires_at
            and self._clock() >= self._expires_at[key]
        ):
            del self._expires_at[key]
            del self._data[key]

    def _expire_batch(self) -> int:
        """Inspect up to _batch_size TTL keys and remove expired entries.

        Move unexpired keys to the back.
        Inspect each key at most once per call.
        Return the number of keys removed.
        """
        with self._lock:
            checks = min(self._batch_size, len(self._expires_at))
            keys_removed = 0

            for _ in range(checks):
                key = next(iter(self._expires_at))
                self._expire_if_needed(key)

                if key not in self._expires_at:
                    keys_removed += 1
                else:
                    self._expires_at.move_to_end(key)

            return keys_removed

    def scan_prefix(self, prefix: str) -> list[tuple[str, str]]:
        """Return non-expired key-value pairs whose keys start with prefix.

        Results are sorted by key in ascending order.
        An empty prefix matches all non-expired keys.
        Return an empty list if nothing matches.
        """
        with self._lock:
            now = self._clock()
            matches = []

            for key, value in self._data.items():
                if not key.startswith(prefix):
                    continue

                deadline = self._expires_at.get(key)
                if deadline is not None and now >= deadline:
                    continue

                matches.append((key, value))

        matches.sort(key=lambda pair: pair[0])
        return matches

