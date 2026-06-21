"""Risk Manager agent — vets a proposed trade against the desk's risk posture."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from trading_agent.agents.toolsets import RISK_TOOLS, binance_toolset
from trading_agent.config import get_settings

INSTRUCTION = """\
You are the Risk Manager on a crypto trading desk. You are the gatekeeper.

Your job: given the Market Analyst's thesis, decide whether a proposed trade is
acceptable BEFORE it goes to execution. You CANNOT place trades.

Workflow:
1. Call get_risk_status to read the hard limits and today's usage (orders placed,
   realized loss, allowed symbols, kill-switch state).
2. Call get_balances and get_open_orders to understand current exposure.
3. Evaluate the proposed trade against the limits and current posture.

Output a clear verdict:
- verdict: APPROVE / REJECT / RESIZE
- if RESIZE, give a specific smaller quantity that fits within limits
- reasons: cite the specific limit or exposure figure driving your decision

Remember: the system also enforces these limits in code, but your job is to catch
bad trades early and size them sensibly. Be conservative when uncertain.
"""


def build_risk_manager() -> LlmAgent:
    return LlmAgent(
        name="risk_manager",
        model=get_settings().adk_model,
        description="Vets proposed trades against hard risk limits and current exposure. Cannot trade.",
        instruction=INSTRUCTION,
        tools=[binance_toolset(RISK_TOOLS)],
        output_key="risk_verdict",
    )
