# Webhook Inbox Lab

Receive signed webhook deliveries in a durable SQLite inbox. An authenticated retry gets the original delivery status without creating a second work item.

## Reproduce the case

Requires Python 3.11+. All examples use synthetic data and run locally with the standard library. Run from the repository root.

```sh
python demo.py
```

The demo opens a temporary inbox, accepts a delivery, closes the connection and retries the same request after reopening it. It prints accepted, duplicate, invalid_signature, then confirms one stored row.

## Design and limits

The protocol signs the timestamp, delivery ID and raw body with HMAC-SHA256. IDs use a restricted ASCII alphabet. Verification runs before database access. The primary key serializes competing requests, while the payload and its digest are recorded in the same transaction. Reusing an ID with different signed content returns conflict. This is a library for a trusted HTTP adapter. The adapter must cap request sizes before buffering, protect its key, and map responses to the sender’s retry policy. Inbox deduplication ends at the database boundary; downstream workers still need idempotent side effects.

## Verification

```sh
python -m unittest discover -s tests -v
```

Regression tests exercise body tampering, freshness, ID substitution, conflicting reuse and concurrent deliveries through independent SQLite connections.
