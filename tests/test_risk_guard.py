"""Tests for the deterministic risk guard — the heart of the security story."""

from __future__ import annotations

from trading_agent.config import Settings
from trading_agent.security.risk_guard import RiskGuard


def _guard(tmp_path, **overrides) -> RiskGuard:
    defaults = dict(
        RISK_ALLOWED_SYMBOLS="BTCUSDT,ETHUSDT",
        RISK_MAX_NOTIONAL_USDT=100,
        RISK_MAX_OPEN_NOTIONAL_USDT=300,
        RISK_MAX_DAILY_LOSS_USDT=50,
        RISK_MAX_ORDERS_PER_DAY=3,
        TRADING_ENABLED=True,
    )
    defaults.update(overrides)
    return RiskGuard(Settings(**defaults), state_path=str(tmp_path / "state.json"))


def test_approves_valid_order(tmp_path):
    d = _guard(tmp_path).check_order("BTCUSDT", "BUY", 50)
    assert d.approved and d.reasons == []


def test_rejects_disallowed_symbol(tmp_path):
    d = _guard(tmp_path).check_order("DOGEUSDT", "BUY", 10)
    assert not d.approved
    assert any("SYMBOL_NOT_ALLOWED" in r for r in d.reasons)


def test_rejects_oversized_notional(tmp_path):
    d = _guard(tmp_path).check_order("BTCUSDT", "BUY", 150)
    assert not d.approved
    assert any("MAX_NOTIONAL_EXCEEDED" in r for r in d.reasons)


def test_rejects_excess_open_exposure(tmp_path):
    d = _guard(tmp_path).check_order("BTCUSDT", "BUY", 80, current_open_notional_usdt=250)
    assert not d.approved
    assert any("MAX_OPEN_EXPOSURE_EXCEEDED" in r for r in d.reasons)


def test_master_kill_switch(tmp_path):
    d = _guard(tmp_path, TRADING_ENABLED=False).check_order("BTCUSDT", "BUY", 10)
    assert not d.approved
    assert any("TRADING_DISABLED" in r for r in d.reasons)


def test_daily_order_limit(tmp_path):
    g = _guard(tmp_path, RISK_MAX_ORDERS_PER_DAY=2)
    g.register_fill(10)
    g.register_fill(10)
    d = g.check_order("BTCUSDT", "BUY", 10)
    assert not d.approved
    assert any("DAILY_ORDER_LIMIT" in r for r in d.reasons)


def test_daily_loss_kill_switch(tmp_path):
    g = _guard(tmp_path, RISK_MAX_DAILY_LOSS_USDT=20)
    g.register_fill(10, realized_pnl_usdt=-25)  # blew through the daily loss cap
    d = g.check_order("BTCUSDT", "BUY", 10)
    assert not d.approved
    assert any("DAILY_LOSS_KILL_SWITCH" in r for r in d.reasons)


def test_state_persists_across_instances(tmp_path):
    g1 = _guard(tmp_path, RISK_MAX_ORDERS_PER_DAY=1)
    g1.register_fill(10)
    # A fresh guard (simulating a restart) must see the spent budget.
    g2 = _guard(tmp_path, RISK_MAX_ORDERS_PER_DAY=1)
    d = g2.check_order("BTCUSDT", "BUY", 10)
    assert not d.approved
    assert any("DAILY_ORDER_LIMIT" in r for r in d.reasons)
