class KeyNotFoundError(KeyError):
    """Raised when an operation requires a key that does not exist."""


class KVStore:
    """A key-value store with string keys and string values."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        """Insert a value, replacing any existing value for the key."""
        self._data[key] = value

    def get(self, key: str) -> str:
        """Return the value, or raise KeyNotFoundError if the key is missing."""
        if key not in self._data:
            raise KeyNotFoundError(key)
        return self._data[key]

    def delete(self, key: str) -> None:
        """Remove the key, or raise KeyNotFoundError if it is missing."""
        if key not in self._data:
            raise KeyNotFoundError(key)
        del self._data[key]
