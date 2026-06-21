"""Coordinator — the orchestrator that runs the trading desk.

Two compositions are offered over the same three specialists:

* ``build_coordinator`` — an LLM-driven Desk Lead that calls each specialist as
  a *tool* (the ADK "agents as tools" pattern). Because an AgentTool returns
  control to the caller once the specialist finishes, the Desk Lead can reliably
  chain analyst -> risk -> execution in a single turn. (Plain ``sub_agents``
  transfer control *to* a specialist and do not return, which stalls the chain.)
* ``build_pipeline`` — a deterministic SequentialAgent (analyst -> risk ->
  execution) for reproducible, audit-friendly runs.

Specialists are rebuilt per composition because ADK assigns each agent a single
parent; sharing one instance across two trees is not allowed.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool

from trading_agent.agents.execution_trader import build_execution_trader
from trading_agent.agents.market_analyst import build_market_analyst
from trading_agent.agents.risk_manager import build_risk_manager
from trading_agent.config import get_settings

COORDINATOR_INSTRUCTION = """\
You are the Desk Lead coordinating a crypto trading desk. You do NOT analyze or
trade yourself — you call your three specialist tools and chain their results.

Your specialist tools:
- market_analyst: researches live data and returns a BUY/SELL/HOLD thesis.
- risk_manager: vets and sizes a proposed trade against hard risk limits.
- execution_trader: places risk-approved orders on the testnet.

Standard workflow for a trade request (do these in order, in ONE turn):
1. Call market_analyst with the symbol to get a thesis.
2. If the user wants to trade (or the thesis is actionable BUY/SELL), call
   risk_manager, passing the proposed symbol, side, and quantity plus the
   analyst's thesis, to get a verdict (APPROVE / RESIZE / REJECT).
3. If the verdict is APPROVE or RESIZE, call execution_trader with the final
   approved symbol, side, and quantity. If REJECT, do not trade.
4. Summarize for the user: thesis, risk verdict, and execution result.

If the user only asks for analysis or a price, call just market_analyst.
Always finish with a clear, concise summary of what each specialist concluded.
"""


def build_coordinator() -> LlmAgent:
    return LlmAgent(
        name="desk_lead",
        model=get_settings().adk_model,
        description="Coordinates the market analyst, risk manager, and execution trader.",
        instruction=COORDINATOR_INSTRUCTION,
        tools=[
            AgentTool(agent=build_market_analyst()),
            AgentTool(agent=build_risk_manager()),
            AgentTool(agent=build_execution_trader()),
        ],
    )


def build_pipeline() -> SequentialAgent:
    """Deterministic analyst -> risk -> execution pipeline sharing session state."""
    return SequentialAgent(
        name="trading_pipeline",
        description="Runs analysis, risk vetting, and execution in a fixed order.",
        sub_agents=[
            build_market_analyst(),
            build_risk_manager(),
            build_execution_trader(),
        ],
    )


# ADK's `adk web` / `adk run` looks for a module-level `root_agent`.
root_agent = build_coordinator()
