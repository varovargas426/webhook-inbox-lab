"""Verify and persist a delivery. Timestamps are Unix seconds."""
import hashlib
import hmac
import re
import sqlite3

SCHEMA = """CREATE TABLE IF NOT EXISTS inbox (
    id TEXT PRIMARY KEY, signed_at INTEGER NOT NULL,
    digest TEXT NOT NULL, body BLOB NOT NULL
)"""


def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.execute(SCHEMA)
    return db


def signature(key, timestamp, delivery, body):
    prefix = f"v1.{timestamp}.{delivery}.".encode("ascii")
    return hmac.new(key, prefix + body, hashlib.sha256).hexdigest()


def receive(db, key, timestamp, delivery, body, supplied, now):
    if not isinstance(delivery, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,96}", delivery):
        return "invalid_id"
    if type(timestamp) is not int or abs(timestamp - now) > 300:
        return "stale"
    if len(body) > 1024 * 1024:
        return "too_large"
    if not isinstance(supplied, str) or not re.fullmatch(r"[a-f0-9]{64}", supplied):
        return "invalid_signature"
    if not hmac.compare_digest(signature(key, timestamp, delivery, body), supplied):
        return "invalid_signature"
    digest = hashlib.sha256(body).hexdigest()
    with db:
        insert = db.execute("INSERT INTO inbox VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
                            (delivery, timestamp, digest, body))
        if insert.rowcount:
            return "accepted"
        old, = db.execute("SELECT digest FROM inbox WHERE id = ?", (delivery,)).fetchone()
        return "duplicate" if old == digest else "conflict"
