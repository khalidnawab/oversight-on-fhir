import threading
from collections import deque
from datetime import datetime, timezone

_MAX_ENTRIES = 200


class FhirActivityLog:
    """Thread-safe in-memory ring buffer of FHIR requests, feeding the UI activity panel.
    Deliberately ephemeral (demo affordance) — the durable record is the FHIR server itself."""

    def __init__(self, maxlen: int = _MAX_ENTRIES):
        self._entries: deque = deque(maxlen=maxlen)
        self._seq = 0
        self._lock = threading.Lock()

    def append(self, method: str, target: str, status: int | None,
               resource_id: str | None = None) -> None:
        with self._lock:
            self._seq += 1
            self._entries.append({
                "seq": self._seq,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "method": method,
                "target": target,
                "status": status,
                "kind": "read" if method == "GET" else "write",
                "resource_id": resource_id,
            })

    def since(self, seq: int) -> list[dict]:
        with self._lock:
            return [e for e in self._entries if e["seq"] > seq]

    def snapshot(self, seq: int) -> tuple[list[dict], int]:
        """Entries after `seq` and the latest seq, read atomically — a poller that
        advances its cursor to the returned seq can never skip an entry."""
        with self._lock:
            return [e for e in self._entries if e["seq"] > seq], self._seq

    @property
    def latest(self) -> int:
        with self._lock:
            return self._seq

    def clear(self) -> None:
        # seq is NOT reset: pollers hold `since` cursors that must stay monotonic.
        with self._lock:
            self._entries.clear()


activity_log = FhirActivityLog()
