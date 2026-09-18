import pytest

from kv_store import KVStore, KeyNotFoundError
from tests.utils import FakeClock

@pytest.fixture
def store() -> KVStore:
    return KVStore()


def test_set_and_get(store: KVStore) -> None:
    store.set("name", "alice")

    assert store.get("name") == "alice"


def test_set_overwrites_existing_value(store: KVStore) -> None:
    store.set("name", "alice")
    store.set("name", "bob")

    assert store.get("name") == "bob"


def test_get_missing_key_raises(store: KVStore) -> None:
    with pytest.raises(KeyNotFoundError):
        store.get("missing")


def test_set_delete_get_missing_key_raises(store: KVStore) -> None:
    store.set("name", "alice")
    store.delete("name")

    with pytest.raises(KeyNotFoundError):
        store.get("name")


def test_delete_missing_key_raises(store: KVStore) -> None:
    with pytest.raises(KeyNotFoundError):
        store.delete("missing")


def test_set_and_get_empty_key(store: KVStore) -> None:
    store.set("", "empty")
    assert store.get("") == "empty"


def test_set_and_get_empty_value(store: KVStore) -> None:
    store.set("empty", "")
    assert store.get("empty") == ""


def test_independent_keys(store: KVStore) -> None:
    store.set("name1", "alice")
    store.set("name2", "bob")
    store.set("name1", "charlie")

    assert store.get("name2") == "bob"

    store.delete("name2")

    assert store.get("name1") == "charlie"


def test_key_expires_at_deadline() -> None:
    clock = FakeClock()
    store = KVStore(clock=clock)

    store.set("name", "alice", ttl_ms=100)

    clock.advance(99)
    assert store.get("name") == "alice"

    clock.advance(1)
    with pytest.raises(KeyNotFoundError):
        store.get("name")

def test_no_ttl_not_in_expires_dict() -> None:
    clock = FakeClock()
    store = KVStore(clock=clock)

    store.set("name", "bob")
    assert "name" not in store._expires_at

    clock.advance(10000)
    assert store.get("name") == "bob"

def test_negative_ttl_raises() -> None:
    clock = FakeClock()
    store = KVStore(clock=clock)
    with pytest.raises(ValueError):
        store.set("name", "bob", -1)

def test_overwrite_ttl_key_without_ttl() -> None:
    clock = FakeClock()
    store = KVStore(clock=clock)

    store.set("name", "alice", 100)
    assert "name" in store._expires_at

    store.set("name", "bob")

    assert store.get("name") == "bob"
    assert "name" not in store._expires_at

def test_delete_expired_key_raises_and_cleans_up() -> None:
    clock = FakeClock()
    store = KVStore(clock=clock)

    store.set("name", "alice", ttl_ms=100)
    clock.advance(100)

    with pytest.raises(KeyNotFoundError):
        store.delete("name")

    assert "name" not in store._data
    assert "name" not in store._expires_at