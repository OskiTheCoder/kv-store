from collections.abc import Callable
from threading import Event, Thread

from kv_store import KVStore, wall_clock_ms


class KVStoreRuntime:
    """Own a store and automatically run periodic expiration."""

    def __init__(
        self,
        *,
        clock: Callable[[], int] = wall_clock_ms,
        cleanup_interval_ms: int = 100,
    ) -> None:
        if cleanup_interval_ms <= 0:
            raise ValueError("cleanup_interval_ms must be > 0")

        self._store = KVStore(clock=clock)
        self._cleanup_interval_s = cleanup_interval_ms / 1000
        self._stop_event = Event()

        self._cleanup_thread = Thread(
            target=self._cleanup_loop,
            name="kv-store-cleanup",
            daemon=True,
        )

        # Start only after all runtime state has been initialized.
        self._cleanup_thread.start()

    @property
    def store(self) -> KVStore:
        """Return the storage engine owned by this runtime."""
        return self._store

    def _cleanup_loop(self) -> None:
        """Run cleanup batches until shutdown is requested."""
        while not self._stop_event.wait(self._cleanup_interval_s):
            self._store._expire_batch()

    def close(self) -> None:
        """Stop maintenance and wait for the worker to finish.

        Safe to call more than once.
        """
        self._stop_event.set()
        self._cleanup_thread.join()