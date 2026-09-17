from collections.abc import Callable
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
        self._expires_at: dict[str, int] = {}
        self._clock = clock

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
        # TODO: Validate TTL before changing either dictionary.
        # TODO: Calculate the deadline using self._clock() + ttl_ms,
        #       if a TTL was provided.
        # TODO: Store the value.
        # TODO: Set the deadline, or remove any previous deadline.
        raise NotImplementedError

    def get(self, key: str) -> str:
        """Return the value, or raise KeyNotFoundError if missing or expired."""
        self._expire_if_needed(key)

        if key not in self._data:
            raise KeyNotFoundError(key)

        return self._data[key]

    def delete(self, key: str) -> None:
        """Remove the key, or raise KeyNotFoundError if missing or expired."""
        self._expire_if_needed(key)

        if key not in self._data:
            raise KeyNotFoundError(key)

        del self._data[key]
        self._expires_at.pop(key, None)

    def _expire_if_needed(self, key: str) -> None:
        """Remove the key from both dictionaries if now >= its deadline."""
        # TODO: If the key has no deadline, do nothing.
        # TODO: If self._clock() >= deadline, remove it
        #       from both dictionaries.
        raise NotImplementedError