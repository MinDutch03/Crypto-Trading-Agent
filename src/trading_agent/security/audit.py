"""Append-only audit log.

Every consequential event — a risk decision, an order, a rejection — is
written as one JSON object per line (JSONL). The log is append-only and
includes a running hash chain so that tampering with any past record
invalidates every record after it (tamper-evident, like a mini blockchain).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return GENESIS
        last = None
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last = line
        if not last:
            return GENESIS
        try:
            return json.loads(last)["hash"]
        except (json.JSONDecodeError, KeyError):
            return GENESIS

    def record(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        prev = self._last_hash()
        entry = {
            "ts": _utc_now_iso(),
            "event": event,
            "payload": payload,
            "prev_hash": prev,
        }
        digest = hashlib.sha256(
            (prev + json.dumps(entry, sort_keys=True)).encode("utf-8")
        ).hexdigest()
        entry["hash"] = digest
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        return entry

    def verify(self) -> bool:
        """Re-walk the chain and confirm no record was altered."""
        if not self.path.exists():
            return True
        prev = GENESIS
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("prev_hash") != prev:
                    return False
                stored = entry.pop("hash")
                recomputed = hashlib.sha256(
                    (prev + json.dumps(entry, sort_keys=True)).encode("utf-8")
                ).hexdigest()
                if stored != recomputed:
                    return False
                prev = stored
        return True
