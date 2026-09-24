from threading import Event

import pytest

from kv_store import KVStore
from runtime import KVStoreRuntime
from tests.utils import FakeClock


def test_runtime_starts_worker_automatically() -> None:
    runtime = KVStoreRuntime()
    try:
        assert isinstance(runtime.store, KVStore)
        assert runtime._cleanup_thread.is_alive()
    finally:
        runtime.close()


def test_runtime_removes_expired_keys_automatically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    cleanup_completed = Event()
    original_expire_batch = KVStore._expire_batch

    def observed_expire_batch(store: KVStore) -> int:
        # run the actual cleanup, then notify the test if it removed a key.
        removed = original_expire_batch(store)
        if removed > 0:
            cleanup_completed.set()
        return removed

    # install before constructing the runtime, which starts its worker.
    monkeypatch.setattr(KVStore, "_expire_batch", observed_expire_batch)

    runtime = KVStoreRuntime(clock=clock, cleanup_interval_ms=10)
    try:
        runtime.store.set("temporary", "alice", ttl_ms=100)
        runtime.store.set("permanent", "bob")

        # coordinate the fake clock update with worker access to the clock.
        with runtime.store._lock:
            clock.advance(100)

        assert cleanup_completed.wait(timeout=2), (
            "Background cleanup did not remove the expired key"
        )

        # inspect storage directly so get() cannot hide a cleanup failure.
        with runtime.store._lock:
            assert "temporary" not in runtime.store._data
            assert "temporary" not in runtime.store._expires_at
            assert runtime.store._data["permanent"] == "bob"
    finally:
        runtime.close()


def test_close_stops_worker() -> None:
    runtime = KVStoreRuntime()
    try:
        runtime.close()

        assert runtime._stop_event.is_set()
        assert not runtime._cleanup_thread.is_alive()
    finally:
        runtime.close()


def test_close_can_be_called_repeatedly() -> None:
    runtime = KVStoreRuntime()
    try:
        runtime.close()
        runtime.close()

        assert not runtime._cleanup_thread.is_alive()
    finally:
        runtime.close()


def test_store_remains_usable_after_runtime_closes() -> None:
    runtime = KVStoreRuntime()
    try:
        runtime.store.set("name", "alice")
    finally:
        runtime.close()

    assert runtime.store.get("name") == "alice"

    runtime.store.set("name", "bob")
    assert runtime.store.get("name") == "bob"


@pytest.mark.parametrize("interval_ms", [0, -1])
def test_nonpositive_cleanup_interval_raises(interval_ms: int) -> None:
    with pytest.raises(ValueError):
        KVStoreRuntime(cleanup_interval_ms=interval_ms)