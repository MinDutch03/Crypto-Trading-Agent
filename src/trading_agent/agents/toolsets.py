"""MCP toolset factory.

Every agent reaches Binance only through the MCP server, launched here as a
stdio subprocess. Each agent receives a `tool_filter` so it sees exactly the
tools its role needs and nothing more — least privilege at the tool layer.
"""

from __future__ import annotations

import os
import sys

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Read-only market-data tools — safe for analysis agents.
MARKET_TOOLS = ["get_price", "get_klines", "get_order_book", "get_24h_stats"]
# Risk-introspection tools.
RISK_TOOLS = ["get_risk_status", "get_open_orders", "get_balances"]
# Trading tools — only the execution agent gets these.
TRADE_TOOLS = ["place_market_order", "cancel_order", "get_open_orders", "get_balances"]


def binance_toolset(tool_filter: list[str]) -> McpToolset:
    """Build an McpToolset that launches our Binance MCP server over stdio."""
    project_root = os.getcwd()
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "trading_agent.binance_mcp.server"],
                env=os.environ.copy(),
                cwd=project_root,
            ),
        ),
        tool_filter=tool_filter,
    )
