# kv store

a python key-value store built to practice storage systems, expiration, and concurrency.

## implemented

- `set`, `get`, and `delete` with string keys and values
- optional ttl in milliseconds, using wall-clock expiration timestamps
- lazy expiration on reads and deletes
- bounded batch expiration using an ordered dictionary
- a separate runtime that automatically starts background cleanup and supports shutdown
- locking around storage operations
- prefix search with sorted results, excluding expired keys
- tests for storage behavior, expiration, and runtime lifecycle

## running tests

```bash
python -m pytest
```

## current limitations

- in-memory only; data is lost when the process exits
- prefix search scans all keys while holding the store lock
- cleanup uses a fixed interval and batch size
- no network interface or transactions

## possible next steps

- capacity limits and lru eviction
- persistence and crash recovery
- transactions
- adaptive expiration cleanup
- a server interface for remote clients
