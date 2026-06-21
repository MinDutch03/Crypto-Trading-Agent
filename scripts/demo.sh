#!/usr/bin/env bash
# =============================================================================
# Sentinel Desk — recordable demo runner
#
# Drives the showcase end-to-end with clear section banners and pauses so you
# can screen-record at your own pace. Press Enter to advance each scene.
#
# Usage:
#   ./scripts/demo.sh                 # interactive, pauses between scenes
#   AUTO=1 ./scripts/demo.sh          # no pauses (for a dry run)
#
# Tip: the free Gemini tier allows ~20 requests/day per model. The default
# model here is flash-lite for demo reliability; override with ADK_MODEL.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

export ADK_MODEL="${ADK_MODEL:-gemini-2.5-flash-lite}"

# Activate venv if present.
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

BOLD=$'\033[1m'; CYAN=$'\033[36m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'

banner() { echo; echo "${BOLD}${CYAN}========================================================${RESET}"; echo "${BOLD}${CYAN}  $1${RESET}"; echo "${BOLD}${CYAN}========================================================${RESET}"; echo; }
say_cmd() { echo "${YELLOW}\$ $*${RESET}"; }
pause() { if [[ "${AUTO:-0}" != "1" ]]; then read -r -p "${GREEN}↵ Press Enter for the next scene...${RESET}"; fi; }

banner "Sentinel Desk — multi-agent crypto trading on Binance (Google ADK)"
echo "Model: ${ADK_MODEL}"
echo "Orders execute on the Binance TESTNET. No real money is at risk."
pause

# ---------------------------------------------------------------------------
banner "Scene 1 — A simple question (coordinator delegates to the analyst)"
say_cmd trading-agent \"What is the current price of BTCUSDT?\"
trading-agent "What is the current price of BTCUSDT?" 2>/dev/null
pause

# ---------------------------------------------------------------------------
banner "Scene 2 — Full trade: analyst -> risk -> execution (deterministic pipeline)"
say_cmd trading-agent --mode pipeline \"Evaluate BTCUSDT and buy 0.001 BTC if risk-compliant\"
trading-agent --mode pipeline "Evaluate BTCUSDT and buy 0.001 BTC if it is a reasonable, risk-compliant entry. Be concise." 2>/dev/null
pause

# ---------------------------------------------------------------------------
banner "Scene 3 — The hard risk guard blocks bad orders (bypassing the agents)"
echo "Calling the trade tool DIRECTLY, as if an agent were compromised:"
python - <<'PY'
import warnings; warnings.filterwarnings("ignore")
from trading_agent.binance_mcp.server import place_market_order, get_risk_status
print("\n• Oversized order (0.01 BTC ~ $640, single-order cap is $100):")
print(" ", place_market_order("BTCUSDT", "BUY", 0.01))
print("\n• Disallowed symbol (DOGEUSDT not in the allow-list):")
print(" ", place_market_order("DOGEUSDT", "BUY", 1))
print("\n• Risk status (note: rejected orders did NOT increment the daily counter):")
import json; print(" ", json.dumps(get_risk_status(), indent=2))
PY
pause

# ---------------------------------------------------------------------------
banner "Scene 4 — Tamper-evident audit log (SHA-256 hash chain)"
python - <<'PY'
import json
from trading_agent.security.audit import AuditLog
from trading_agent.config import get_settings
log = AuditLog(get_settings().audit_log_path)
print("Recent audit entries:")
for line in list(open(log.path))[-6:]:
    e = json.loads(line)
    print(f"  {e['ts'][11:19]}  {e['event']:16}  {json.dumps(e['payload'])[:80]}")
print("\nHash-chain integrity verify():", log.verify())
PY
pause

banner "Deploy: 'docker compose up' serves the ADK web UI on :8000 | CI+CD are green | image on GHCR"
echo "Thanks for watching Sentinel Desk."
