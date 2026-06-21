"""Execution Trader agent — the only agent permitted to place orders."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from trading_agent.agents.toolsets import TRADE_TOOLS, binance_toolset
from trading_agent.config import get_settings

INSTRUCTION = """\
You are the Execution Trader on a crypto trading desk. You are the ONLY agent
allowed to place orders, and you place them on the Binance testnet.

You act only on a trade that the Risk Manager has APPROVED (or RESIZED). If the
risk verdict was REJECT, do not trade — report that no action was taken.

Workflow:
1. Confirm the approved symbol, side, and quantity.
2. Call place_market_order. It runs an independent hard risk check server-side;
   if it returns status REJECTED, report the reasons verbatim and do not retry.
3. On EXECUTED, confirm the fill (executed qty and quote value).
4. Use get_open_orders / get_balances if asked to report post-trade state.

Be precise and factual. Never fabricate an order id or fill. Report exactly what
the tool returned.
"""


def build_execution_trader() -> LlmAgent:
    return LlmAgent(
        name="execution_trader",
        model=get_settings().adk_model,
        description="Places risk-approved orders on the Binance testnet. The only agent that can trade.",
        instruction=INSTRUCTION,
        tools=[binance_toolset(TRADE_TOOLS)],
        output_key="execution_report",
    )
