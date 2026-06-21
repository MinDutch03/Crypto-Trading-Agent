#!/usr/bin/env bash
# =============================================================================
# Generate the male-voice narration track for the demo video (macOS `say`).
#
# Produces one audio file per scene in docs/voiceover/ plus a combined track,
# so you can drop each clip onto the matching scene in your editor.
#
# Usage:
#   ./scripts/voiceover.sh                 # default voice: Daniel (en_GB male)
#   VOICE="Reed (English (US))" ./scripts/voiceover.sh
#   RATE=170 ./scripts/voiceover.sh        # words per minute
#
# List installed voices with:  say -v '?'
# For a higher-quality male voice, install "Tom"/"Alex" (Enhanced) via
# System Settings → Accessibility → Spoken Content → System Voice → Manage.
# Or generate the track with ElevenLabs and skip this script.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

VOICE="${VOICE:-Daniel}"
RATE="${RATE:-160}"
OUT="docs/voiceover"
mkdir -p "$OUT"

gen() {  # gen <index> <name> <text>
  local idx="$1" name="$2" text="$3"
  local aiff="$OUT/${idx}_${name}.aiff" m4a="$OUT/${idx}_${name}.m4a"
  echo "→ scene ${idx} (${name})"
  say -v "$VOICE" -r "$RATE" -o "$aiff" "$text"
  if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -y -loglevel error -i "$aiff" -c:a aac -b:a 128k "$m4a" && rm -f "$aiff"
  fi
}

gen 0 problem "Letting an A.I. agent trade crypto is exciting and terrifying. Exciting, because it can watch the market and act in seconds. Terrifying, because language models are non-deterministic, and money is very deterministic. One hallucinated number can drain an account. So the real question isn't can an agent trade. It's whether it can trade under controls a business would actually sign off on. That's Sentinel Desk."

gen 1 architecture "Sentinel Desk is a multi-agent trading desk built on Google's Agent Development Kit. Like a real desk, it separates duties. A Market Analyst researches live Binance data. A Risk Manager vets and sizes the trade. An Execution Trader is the only agent allowed to place orders. A Desk Lead coordinates them. Every agent reaches Binance through one M.C.P. server, and each agent only sees the tools its role needs. The analyst literally has no trade tool. The security lives in code, at the tool boundary, not in a prompt."

gen 2 query "Let's run it. I'll ask for a price. The Desk Lead delegates to the Market Analyst, which calls the get-price tool on the M.C.P. server, and answers with live data. Notice it routed to the right specialist on its own."

gen 3 trade "Now a real trade. The analyst reads price, daily stats, and candles, and forms a thesis. The Risk Manager checks the order against hard limits: notional size, open exposure, daily caps, and approves it, item by item. Only then does the Execution Trader place the order, on the Binance testnet. There's the fill: a real order I.D., a real quantity. Three specialists, one clean hand-off."

gen 4 security "But what if an agent goes rogue, or a prompt injection tries to force a bad trade? I'll bypass the agents entirely and call the trade tool directly. First, an order ten times too big: six hundred dollars against a hundred-dollar cap. Rejected, with the exact reason. Now a symbol that isn't on the allow-list. Rejected again. These limits are deterministic Python. The model can reason about risk, but it cannot override it. And rejected orders never even count against the daily budget."

gen 5 audit "Every decision and every fill is written to an append-only audit log, chained together with SHA-256 hashes. If anyone edits a past record, the chain breaks. Here's the verification passing: a log you can actually prove wasn't tampered with."

gen 6 close "It's built to ship. One docker compose up serves the agent UI in the browser. Continuous integration runs the tests and builds the image. Continuous deployment publishes it to the container registry on every merge. Multi-agent orchestration, an M.C.P. server, a real security layer, and a deployment pipeline. Sentinel Desk. Thanks for watching."

# Combined track (in scene order) if ffmpeg is available.
if command -v ffmpeg >/dev/null 2>&1; then
  ls "$OUT"/*.m4a >/dev/null 2>&1 && {
    printf "file '%s'\n" "$OUT"/*.m4a | sed "s|$OUT/|./|" > "$OUT/_concat.txt"
    (cd "$OUT" && ffmpeg -y -loglevel error -f concat -safe 0 -i _concat.txt -c copy narration_full.m4a)
    rm -f "$OUT/_concat.txt"
    echo "✓ combined track: $OUT/narration_full.m4a"
  }
fi
echo "Done. Per-scene clips and narration_full.m4a are in $OUT/"
