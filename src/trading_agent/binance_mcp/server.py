"""Binance MCP server.

Exposes the Binance API as a set of Model Context Protocol tools over stdio,
built with FastMCP. The ADK agents connect to this server as an MCP client and
call these tools — they never import the Binance SDK directly.

Security is enforced *here*, at the tool boundary, not just in the agents:

* market-data tools are read-only and hit live Binance;
* ``place_market_order`` runs every order through the :class:`RiskGuard` and
  writes the decision to the tamper-evident :class:`AuditLog` before anything
  touches the exchange. A rejected order never reaches Binance.

Run directly for stdio transport:  ``python -m trading_agent.binance_mcp.server``
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from trading_agent.binance_mcp import client as bz
from trading_agent.config import get_settings
from trading_agent.security.audit import AuditLog
from trading_agent.security.risk_guard import RiskGuard

settings = get_settings()
clients = bz.build_clients(settings)
guard = RiskGuard(settings)
audit = AuditLog(settings.audit_log_path)

mcp = FastMCP("binance-trading")


# --------------------------------------------------------------------------
# Market data (read-only)
# --------------------------------------------------------------------------

@mcp.tool()
def get_price(symbol: str) -> dict[str, Any]:
    """Get the current price for a symbol, e.g. BTCUSDT."""
    return bz.get_price(clients, symbol.upper())


@mcp.tool()
def get_klines(symbol: str, interval: str = "1h", limit: int = 50) -> list[dict[str, Any]]:
    """Get OHLCV candlesticks. interval e.g. 1m,5m,1h,4h,1d. limit max 1000."""
    return bz.get_klines(clients, symbol.upper(), interval, min(limit, 1000))


@mcp.tool()
def get_order_book(symbol: str, limit: int = 10) -> dict[str, Any]:
    """Get top-of-book bids/asks for a symbol."""
    return bz.get_order_book(clients, symbol.upper(), limit)


@mcp.tool()
def get_24h_stats(symbol: str) -> dict[str, Any]:
    """Get 24h price-change statistics for a symbol."""
    return bz.get_24h_stats(clients, symbol.upper())


# --------------------------------------------------------------------------
# Account (testnet)
# --------------------------------------------------------------------------

@mcp.tool()
def get_balances() -> list[dict[str, Any]]:
    """Get non-zero balances on the testnet trading account."""
    return bz.get_balances(clients)


@mcp.tool()
def get_open_orders(symbol: str | None = None) -> list[dict[str, Any]]:
    """List open orders, optionally filtered by symbol."""
    return bz.get_open_orders(clients, symbol.upper() if symbol else None)


@mcp.tool()
def get_risk_status() -> dict[str, Any]:
    """Return current risk-limit configuration and today's usage counters."""
    return guard.status()


# --------------------------------------------------------------------------
# Trading (testnet, risk-guarded)
# --------------------------------------------------------------------------

@mcp.tool()
def place_market_order(symbol: str, side: str, quantity: float) -> dict[str, Any]:
    """Place a MARKET order on the testnet after mandatory risk checks.

    Returns the executed order, or a rejection object with the reasons the
    risk guard refused it. side must be BUY or SELL.
    """
    symbol = symbol.upper()

    # 1. Price the order so the guard can reason in USDT notional.
    price = bz.get_price(clients, symbol)["price"]
    notional = price * quantity

    # 2. Current open exposure (sum of resting order notionals).
    open_orders = bz.get_open_orders(clients)
    open_notional = sum(o["price"] * o["orig_qty"] for o in open_orders if o["price"] > 0)

    # 3. Hard risk check — deterministic, non-overridable.
    decision = guard.check_order(symbol, side, notional, open_notional)
    audit.record(
        "risk_decision",
        {
            "symbol": symbol,
            "side": side.upper(),
            "quantity": quantity,
            "notional_usdt": round(notional, 4),
            "decision": decision.as_dict(),
        },
    )
    if not decision.approved:
        return {"status": "REJECTED", "reasons": decision.reasons}

    # 4. Execute on testnet and record the fill.
    order = bz.place_market_order(clients, symbol, side, quantity)
    guard.register_fill(notional)
    audit.record("order_executed", order)
    return {"status": "EXECUTED", "order": order}


@mcp.tool()
def cancel_order(symbol: str, order_id: int) -> dict[str, Any]:
    """Cancel a resting order by id."""
    res = bz.cancel_order(clients, symbol.upper(), order_id)
    audit.record("order_cancelled", res)
    return res


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
