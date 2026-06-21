"""Market Analyst agent — read-only market research and a trade thesis."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from trading_agent.agents.toolsets import MARKET_TOOLS, binance_toolset
from trading_agent.config import get_settings

INSTRUCTION = """\
You are the Market Analyst on a crypto trading desk.

Your job: research a symbol using live Binance market data and produce a concise,
evidence-based trade thesis. You CANNOT place trades — you only analyze.

Workflow:
1. Use get_price and get_24h_stats for the current snapshot.
2. Use get_klines (e.g. interval=1h, limit=50) to read recent trend, momentum,
   support/resistance, and volatility.
3. Optionally use get_order_book to gauge near-term buy/sell pressure.

Output a short structured thesis:
- direction: BUY / SELL / HOLD
- conviction: low / medium / high
- rationale: 2-3 sentences citing the specific numbers you saw
- suggested_symbol and an indicative quantity if you propose a trade

Be disciplined: if the data is choppy or unclear, say HOLD. Never invent numbers.
"""


def build_market_analyst() -> LlmAgent:
    return LlmAgent(
        name="market_analyst",
        model=get_settings().adk_model,
        description="Researches live market data and produces a BUY/SELL/HOLD thesis. Cannot trade.",
        instruction=INSTRUCTION,
        tools=[binance_toolset(MARKET_TOOLS)],
        output_key="market_thesis",
    )
