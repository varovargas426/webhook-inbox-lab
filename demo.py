from contextlib import closing
from pathlib import Path
from secrets import token_bytes
from tempfile import TemporaryDirectory
from inbox import connect, receive, signature


if __name__ == "__main__":
    key, body, stamp, delivery = token_bytes(32), b'{"event":"ticket.opened"}', 1000, "evt_014"
    signed = signature(key, stamp, delivery, body)
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "inbox.sqlite"
        with closing(connect(path)) as db:
            print(receive(db, key, stamp, delivery, body, signed, stamp))
        with closing(connect(path)) as db:
            print(receive(db, key, stamp, delivery, body, signed, stamp + 10))
            print(receive(db, key, stamp, delivery, body + b"!", signed, stamp))
            print("Stored rows:", db.execute("SELECT count(*) FROM inbox").fetchone()[0])
