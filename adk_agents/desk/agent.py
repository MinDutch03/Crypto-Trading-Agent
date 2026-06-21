"""ADK app entrypoint for `adk web` / `adk api_server`.

`adk web adk_agents` discovers this `desk` app and serves the coordinator
(Desk Lead) with its three specialist sub-agents in the browser dev UI.
"""

from trading_agent.agents.coordinator import root_agent  # noqa: F401
