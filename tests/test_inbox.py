from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import tempfile
import unittest
from inbox import connect, receive, signature


class InboxTests(unittest.TestCase):
    def test_authenticated_fields_and_conflict(self):
        with closing(connect(":memory:")) as db:
            key, body = b"test", b"original"
            sig = signature(key, 1000, "a", body)
            for delivery, data, now, expected in [
                ("a", body, 1301, "stale"), ("b", body, 1000, "invalid_signature"),
                ("a", b"altered", 1000, "invalid_signature"), ("a", body, 1300, "accepted")]:
                self.assertEqual(receive(db, key, 1000, delivery, data, sig, now), expected)
            new = signature(key, 1001, "a", b"different")
            self.assertEqual(receive(db, key, 1001, "a", b"different", new, 1001), "conflict")
            self.assertEqual(db.execute("SELECT body FROM inbox").fetchone(), (body,))

    def test_concurrent_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inbox.db"
            with closing(connect(path)):
                pass
            def deliver(_):
                with closing(connect(path)) as db:
                    sig = signature(b"test", 10, "same", b"payload")
                    return receive(db, b"test", 10, "same", b"payload", sig, 10)
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(deliver, range(8)))
            self.assertEqual(results.count("accepted"), 1)
            self.assertEqual(results.count("duplicate"), 7)
