"""Tests for the tamper-evident audit log."""

from __future__ import annotations

import json

from trading_agent.security.audit import AuditLog


def test_records_and_verifies(tmp_path):
    log = AuditLog(str(tmp_path / "a.jsonl"))
    log.record("risk_decision", {"symbol": "BTCUSDT", "approved": True})
    log.record("order_executed", {"order_id": 1})
    assert log.verify() is True


def test_empty_log_verifies(tmp_path):
    log = AuditLog(str(tmp_path / "missing.jsonl"))
    assert log.verify() is True


def test_tampering_is_detected(tmp_path):
    path = tmp_path / "a.jsonl"
    log = AuditLog(str(path))
    log.record("risk_decision", {"symbol": "BTCUSDT", "approved": False})
    log.record("risk_decision", {"symbol": "ETHUSDT", "approved": True})

    # Tamper with the first record's payload, leaving its hash intact.
    lines = path.read_text().splitlines()
    first = json.loads(lines[0])
    first["payload"]["approved"] = True  # flip a rejection into an approval
    lines[0] = json.dumps(first)
    path.write_text("\n".join(lines) + "\n")

    assert log.verify() is False


def test_hash_chain_links_records(tmp_path):
    path = tmp_path / "a.jsonl"
    log = AuditLog(str(path))
    e1 = log.record("a", {"n": 1})
    e2 = log.record("b", {"n": 2})
    assert e2["prev_hash"] == e1["hash"]
