import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timedelta, timezone


class DuplicateAlertStore:
    def __init__(self, path: str, window_seconds: int) -> None:
        self.path = path
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    dedupe_key TEXT PRIMARY KEY,
                    received_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def is_duplicate(self, payload: dict) -> tuple[bool, str]:
        dedupe_key = self._build_key(payload)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)

        with self._lock, sqlite3.connect(self.path) as conn:
            conn.execute(
                "DELETE FROM webhook_events WHERE received_at < ?",
                (cutoff.isoformat(),),
            )

            existing = conn.execute(
                "SELECT dedupe_key FROM webhook_events WHERE dedupe_key = ?",
                (dedupe_key,),
            ).fetchone()
            if existing:
                conn.commit()
                return True, dedupe_key

            conn.execute(
                """
                INSERT INTO webhook_events (dedupe_key, received_at, payload)
                VALUES (?, ?, ?)
                """,
                (
                    dedupe_key,
                    now.isoformat(),
                    json.dumps(payload, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()

        return False, dedupe_key

    @staticmethod
    def _build_key(payload: dict) -> str:
        key_payload = {
            "symbol": payload.get("symbol", ""),
            "window_seconds": payload.get("_duplicate_window_seconds", 0),
        }
        canonical = json.dumps(key_payload, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
