"""Coordinator — the orchestrator that runs the trading desk.

Two compositions are offered over the same three specialists:

* ``build_coordinator`` — an LLM-driven coordinator (root LlmAgent) that decides
  which specialist to delegate to, in the spirit of an autonomous desk lead.
* ``build_pipeline`` — a deterministic SequentialAgent (analyst -> risk ->
  execution) for reproducible, audit-friendly runs.

Specialists are rebuilt per composition because ADK assigns each agent a single
parent; sharing one instance across two trees is not allowed.
"""

from __future__ import annotations

from google.adk.agents import LlmAgent, SequentialAgent

from trading_agent.agents.execution_trader import build_execution_trader
from trading_agent.agents.market_analyst import build_market_analyst
from trading_agent.agents.risk_manager import build_risk_manager
from trading_agent.config import get_settings

COORDINATOR_INSTRUCTION = """\
You are the Desk Lead coordinating a crypto trading desk. You orchestrate three
specialists and you do NOT trade or analyze yourself — you delegate.

Your team:
- market_analyst: researches live data and produces a BUY/SELL/HOLD thesis.
- risk_manager: vets and sizes a proposed trade against hard risk limits.
- execution_trader: places risk-approved orders on the testnet.

Standard workflow for a trade request:
1. Delegate to market_analyst to get a thesis for the symbol.
2. If the thesis is actionable (BUY or SELL), delegate to risk_manager to vet
   and size it.
3. Only if the risk_manager APPROVES (or RESIZEs), delegate to execution_trader
   with the approved symbol/side/quantity.
4. Summarize the outcome for the user: thesis, risk verdict, and execution result.

If the user only asks for analysis or a price, delegate just to market_analyst.
Always finish with a clear, concise summary of what each specialist concluded.
"""


def build_coordinator() -> LlmAgent:
    return LlmAgent(
        name="desk_lead",
        model=get_settings().adk_model,
        description="Coordinates the market analyst, risk manager, and execution trader.",
        instruction=COORDINATOR_INSTRUCTION,
        sub_agents=[
            build_market_analyst(),
            build_risk_manager(),
            build_execution_trader(),
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
