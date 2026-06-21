"""Binance connectivity.

Two strictly separated surfaces so that real funds are never at risk:

* ``market`` — a LIVE client used only for **read-only** market data
  (prices, klines, order book). It uses public endpoints, optionally
  authenticated with read-only keys. It can never place an order.
* ``trader`` — a TESTNET client used for **all** order placement. It talks
  to https://testnet.binance.vision with fake funds.

This split is the foundation of the security story: even a fully
compromised agent cannot move real money, because the only client wired to
trading endpoints points at the testnet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from binance.client import Client

from trading_agent.config import Settings, get_settings


@dataclass
class BinanceClients:
    """Holds the two separated Binance clients."""

    market: Client  # live, read-only market data
    trader: Client  # testnet, order placement
    live_authenticated: bool  # whether read-only live keys were supplied


def build_clients(settings: Settings | None = None) -> BinanceClients:
    settings = settings or get_settings()

    # Live market-data client. Public market endpoints need no auth; if
    # read-only keys are present we pass them so account-data reads work too.
    market = Client(
        api_key=settings.binance_live_api_key or None,
        api_secret=settings.binance_live_api_secret or None,
    )

    # Testnet trading client — the ONLY client allowed to place orders.
    trader = Client(
        api_key=settings.binance_testnet_api_key or None,
        api_secret=settings.binance_testnet_api_secret or None,
        testnet=True,
    )

    return BinanceClients(
        market=market,
        trader=trader,
        live_authenticated=bool(settings.binance_live_api_key),
    )


# --------------------------------------------------------------------------
# Market data (read-only, live)
# --------------------------------------------------------------------------

def get_price(clients: BinanceClients, symbol: str) -> dict[str, Any]:
    t = clients.market.get_symbol_ticker(symbol=symbol)
    return {"symbol": t["symbol"], "price": float(t["price"])}


def get_klines(
    clients: BinanceClients, symbol: str, interval: str = "1h", limit: int = 50
) -> list[dict[str, Any]]:
    raw = clients.market.get_klines(symbol=symbol, interval=interval, limit=limit)
    return [
        {
            "open_time": k[0],
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "close_time": k[6],
        }
        for k in raw
    ]


def get_order_book(clients: BinanceClients, symbol: str, limit: int = 10) -> dict[str, Any]:
    ob = clients.market.get_order_book(symbol=symbol, limit=limit)
    return {
        "symbol": symbol,
        "bids": [[float(p), float(q)] for p, q in ob["bids"]],
        "asks": [[float(p), float(q)] for p, q in ob["asks"]],
    }


def get_24h_stats(clients: BinanceClients, symbol: str) -> dict[str, Any]:
    s = clients.market.get_ticker(symbol=symbol)
    return {
        "symbol": s["symbol"],
        "price_change_percent": float(s["priceChangePercent"]),
        "last_price": float(s["lastPrice"]),
        "high_price": float(s["highPrice"]),
        "low_price": float(s["lowPrice"]),
        "volume": float(s["volume"]),
        "quote_volume": float(s["quoteVolume"]),
    }


# --------------------------------------------------------------------------
# Account & trading (testnet)
# --------------------------------------------------------------------------

def get_balances(clients: BinanceClients) -> list[dict[str, Any]]:
    """Return non-zero testnet balances."""
    acct = clients.trader.get_account()
    out = []
    for b in acct["balances"]:
        free, locked = float(b["free"]), float(b["locked"])
        if free or locked:
            out.append({"asset": b["asset"], "free": free, "locked": locked})
    return out


def get_open_orders(clients: BinanceClients, symbol: str | None = None) -> list[dict[str, Any]]:
    orders = (
        clients.trader.get_open_orders(symbol=symbol)
        if symbol
        else clients.trader.get_open_orders()
    )
    return [
        {
            "symbol": o["symbol"],
            "order_id": o["orderId"],
            "side": o["side"],
            "type": o["type"],
            "price": float(o["price"]),
            "orig_qty": float(o["origQty"]),
            "status": o["status"],
        }
        for o in orders
    ]


def place_market_order(
    clients: BinanceClients, symbol: str, side: str, quantity: float
) -> dict[str, Any]:
    """Place a MARKET order on the **testnet**. Risk checks happen upstream."""
    order = clients.trader.create_order(
        symbol=symbol,
        side=side.upper(),
        type="MARKET",
        quantity=quantity,
    )
    return {
        "symbol": order["symbol"],
        "order_id": order["orderId"],
        "side": order["side"],
        "type": order["type"],
        "status": order["status"],
        "executed_qty": float(order["executedQty"]),
        "cummulative_quote_qty": float(order.get("cummulativeQuoteQty", 0.0)),
    }


def cancel_order(clients: BinanceClients, symbol: str, order_id: int) -> dict[str, Any]:
    res = clients.trader.cancel_order(symbol=symbol, orderId=order_id)
    return {"symbol": res["symbol"], "order_id": res["orderId"], "status": res["status"]}
