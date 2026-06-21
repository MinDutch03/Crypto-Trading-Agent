"""Command-line entrypoint for the trading desk.

Examples:
    trading-agent "Analyze BTCUSDT and, if it's a safe buy, trade a tiny amount"
    trading-agent --mode pipeline "Evaluate ETHUSDT for a 0.01 ETH buy"
    trading-agent --mode coordinator "What's the price of BNBUSDT?"
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from trading_agent.agents.coordinator import build_coordinator, build_pipeline
from trading_agent.config import get_settings

APP_NAME = "crypto-trading-agent"
USER_ID = "desk-operator"
SESSION_ID = "session-1"


def _format_event(event) -> str | None:
    """Render an ADK event into a readable console line for the demo."""
    author = getattr(event, "author", "?")
    lines: list[str] = []
    content = getattr(event, "content", None)
    if content and getattr(content, "parts", None):
        for part in content.parts:
            if getattr(part, "function_call", None):
                fc = part.function_call
                lines.append(f"  → [{author}] calls tool: {fc.name}({dict(fc.args or {})})")
            elif getattr(part, "function_response", None):
                fr = part.function_response
                lines.append(f"  ← [{author}] tool result: {fr.name}")
            elif getattr(part, "text", None) and part.text.strip():
                prefix = "FINAL" if event.is_final_response() else author
                lines.append(f"[{prefix}] {part.text.strip()}")
    return "\n".join(lines) if lines else None


async def run(prompt: str, mode: str) -> None:
    settings = get_settings()
    if not settings.google_api_key:
        print("ERROR: GOOGLE_API_KEY is not set. Copy .env.example to .env and fill it in.",
              file=sys.stderr)
        sys.exit(1)

    agent = build_pipeline() if mode == "pipeline" else build_coordinator()
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    print(f"\n=== Trading desk ({mode}) | model={settings.adk_model} ===")
    print(f"Prompt: {prompt}\n")

    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    try:
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=message
        ):
            line = _format_event(event)
            if line:
                print(line)
    finally:
        await runner.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent Binance trading desk (Google ADK).")
    parser.add_argument("prompt", help="Instruction for the desk, in natural language.")
    parser.add_argument(
        "--mode",
        choices=["coordinator", "pipeline"],
        default="coordinator",
        help="coordinator = LLM-driven delegation; pipeline = fixed analyst->risk->execution order.",
    )
    args = parser.parse_args()
    asyncio.run(run(args.prompt, args.mode))


if __name__ == "__main__":
    main()
