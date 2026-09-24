import pytest

from kv_store import KVStore, KeyNotFoundError
from tests.utils import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(clock: FakeClock) -> KVStore:
    return KVStore(clock=clock)


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


def test_deleted_key_cannot_be_retrieved(store: KVStore) -> None:
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


def test_key_expires_at_deadline(
    store: KVStore, clock: FakeClock
) -> None:
    store.set("name", "alice", ttl_ms=100)

    clock.advance(99)
    assert store.get("name") == "alice"

    clock.advance(1)
    with pytest.raises(KeyNotFoundError):
        store.get("name")

    assert "name" not in store._data
    assert "name" not in store._expires_at


def test_key_without_ttl_does_not_expire(
    store: KVStore, clock: FakeClock
) -> None:
    store.set("name", "bob")

    assert "name" not in store._expires_at

    clock.advance(10_000)

    assert store.get("name") == "bob"


@pytest.mark.parametrize("ttl_ms", [0, -1])
def test_nonpositive_ttl_raises(store: KVStore, ttl_ms: int) -> None:
    with pytest.raises(ValueError):
        store.set("name", "bob", ttl_ms=ttl_ms)

    assert "name" not in store._data
    assert "name" not in store._expires_at


def test_overwrite_ttl_key_without_ttl(
    store: KVStore, clock: FakeClock
) -> None:
    store.set("name", "alice", ttl_ms=100)
    store.set("name", "bob")

    clock.advance(100)

    assert store.get("name") == "bob"
    assert "name" not in store._expires_at


def test_delete_expired_key_raises_and_cleans_up(
    store: KVStore, clock: FakeClock
) -> None:
    store.set("name", "alice", ttl_ms=100)
    clock.advance(100)

    with pytest.raises(KeyNotFoundError):
        store.delete("name")

    assert "name" not in store._data
    assert "name" not in store._expires_at


def test_expire_batch_expires_keys(
    store: KVStore, clock: FakeClock
) -> None:
    store.set("name", "alice", ttl_ms=1000)
    store.set("foo", "bar", ttl_ms=2000)
    store.set("hello", "world", ttl_ms=10)

    clock.advance(9)

    assert store._expire_batch() == 0
    assert len(store._data) == 3

    clock.advance(1)

    assert store._expire_batch() == 1
    assert store._data == {"name": "alice", "foo": "bar"}
    assert "hello" not in store._expires_at


def test_expire_batch_respects_budget_and_rotates(
    store: KVStore, clock: FakeClock
) -> None:
    store._batch_size = 2

    store.set("first", "alice", ttl_ms=1000)
    store.set("second", "bob", ttl_ms=1000)
    store.set("third", "charlie", ttl_ms=10)

    clock.advance(10)

    assert store._expire_batch() == 0
    assert "third" in store._data
    assert list(store._expires_at) == ["third", "first", "second"]

    assert store._expire_batch() == 1
    assert "third" not in store._expires_at
    assert store._data == {"first": "alice", "second": "bob"}

def test_prefix_search_matching_keys(store: KVStore) -> None:
    store.set("user:1", "alice")
    store.set("user:2", "bob")
    store.set("foo", "bar")

    matches = store.scan_prefix("user")
    assert matches == [("user:1", "alice"), ("user:2", "bob")]

def test_prefix_search_excludes_expired_keys(
    store: KVStore, clock: FakeClock
) -> None:
    store.set("user:1", "alice", ttl_ms=100)
    store.set("user:2", "bob")

    clock.advance(100)

    assert store.scan_prefix("user:") == [("user:2", "bob")]


def test_empty_prefix_returns_all_keys_sorted(store: KVStore) -> None:
    store.set("user:2", "bob")
    store.set("foo", "bar")
    store.set("user:1", "alice")

    assert store.scan_prefix("") == [
        ("foo", "bar"),
        ("user:1", "alice"),
        ("user:2", "bob"),
    ]