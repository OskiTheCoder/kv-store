import pytest

from kv_store import KVStore, KeyNotFoundError


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

    
