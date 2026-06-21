"""Risk guard — the hard limit layer between an agent's intent and the market.

No order reaches Binance without passing every check here. The LLM agents can
*reason* about risk, but they cannot *override* it: the limits are enforced in
deterministic Python, loaded from configuration, and backed by daily counters
persisted to disk so a restart can't reset the kill switch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from trading_agent.config import Settings, get_settings


@dataclass
class RiskDecision:
    approved: bool
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"approved": self.approved, "reasons": self.reasons}


class RiskGuard:
    def __init__(self, settings: Settings | None = None, state_path: str = "audit/risk_state.json") -> None:
        self.s = settings or get_settings()
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    # --- daily state -------------------------------------------------------
    def _load_state(self) -> dict:
        today = date.today().isoformat()
        if self.state_path.exists():
            try:
                st = json.loads(self.state_path.read_text())
                if st.get("date") == today:
                    return st
            except (json.JSONDecodeError, OSError):
                pass
        return {"date": today, "orders_today": 0, "realized_loss_today": 0.0}

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self._state, indent=2))

    def _roll_day_if_needed(self) -> None:
        today = date.today().isoformat()
        if self._state.get("date") != today:
            self._state = {"date": today, "orders_today": 0, "realized_loss_today": 0.0}
            self._save_state()

    # --- public API --------------------------------------------------------
    def check_order(
        self,
        symbol: str,
        side: str,
        notional_usdt: float,
        current_open_notional_usdt: float = 0.0,
    ) -> RiskDecision:
        """Evaluate a proposed order against all hard limits."""
        self._roll_day_if_needed()
        reasons: list[str] = []

        if not self.s.trading_enabled:
            reasons.append("TRADING_DISABLED: master kill switch is off")

        if symbol not in self.s.allowed_symbols:
            reasons.append(
                f"SYMBOL_NOT_ALLOWED: {symbol} not in {sorted(self.s.allowed_symbols)}"
            )

        if side.upper() not in {"BUY", "SELL"}:
            reasons.append(f"INVALID_SIDE: {side}")

        if notional_usdt <= 0:
            reasons.append("INVALID_NOTIONAL: must be > 0")

        if notional_usdt > self.s.risk_max_notional_usdt:
            reasons.append(
                f"MAX_NOTIONAL_EXCEEDED: {notional_usdt:.2f} > "
                f"{self.s.risk_max_notional_usdt:.2f} USDT"
            )

        projected_open = current_open_notional_usdt + notional_usdt
        if projected_open > self.s.risk_max_open_notional_usdt:
            reasons.append(
                f"MAX_OPEN_EXPOSURE_EXCEEDED: projected {projected_open:.2f} > "
                f"{self.s.risk_max_open_notional_usdt:.2f} USDT"
            )

        if self._state["orders_today"] >= self.s.risk_max_orders_per_day:
            reasons.append(
                f"DAILY_ORDER_LIMIT: {self._state['orders_today']} >= "
                f"{self.s.risk_max_orders_per_day}"
            )

        if self._state["realized_loss_today"] >= self.s.risk_max_daily_loss_usdt:
            reasons.append(
                f"DAILY_LOSS_KILL_SWITCH: realized loss "
                f"{self._state['realized_loss_today']:.2f} >= "
                f"{self.s.risk_max_daily_loss_usdt:.2f} USDT"
            )

        return RiskDecision(approved=not reasons, reasons=reasons)

    def register_fill(self, notional_usdt: float, realized_pnl_usdt: float = 0.0) -> None:
        """Record that an order executed, updating daily counters."""
        self._roll_day_if_needed()
        self._state["orders_today"] += 1
        if realized_pnl_usdt < 0:
            self._state["realized_loss_today"] += abs(realized_pnl_usdt)
        self._save_state()

    def status(self) -> dict:
        self._roll_day_if_needed()
        return {
            **self._state,
            "limits": {
                "max_notional_usdt": self.s.risk_max_notional_usdt,
                "max_open_notional_usdt": self.s.risk_max_open_notional_usdt,
                "max_daily_loss_usdt": self.s.risk_max_daily_loss_usdt,
                "max_orders_per_day": self.s.risk_max_orders_per_day,
                "allowed_symbols": sorted(self.s.allowed_symbols),
                "trading_enabled": self.s.trading_enabled,
            },
        }
