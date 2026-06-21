# Sentinel Desk — Demo Video Script & Storyboard

**Target length:** ≤ 5 minutes · **Voice:** male (e.g. macOS `Daniel`, or ElevenLabs) · **Pace:** ~150 wpm

Record your screen (QuickTime or OBS) while running `./scripts/demo.sh`, then lay the
narration over it. Each scene below lists what's **on screen**, the **command**, and the
**narration** to read. Narration audio can be generated per-scene with `make voiceover`.

---

### Scene 0 — Title & problem  · ~0:00–0:30
**On screen:** README title / a title card: *"Sentinel Desk — a crypto trading desk you can trust with money."*

> "Letting an AI agent trade crypto is exciting and terrifying. Exciting, because it can watch the market and act in seconds. Terrifying, because language models are non-deterministic, and money is very deterministic. One hallucinated number can drain an account. So the real question isn't *can* an agent trade — it's whether it can trade under controls a business would actually sign off on. That's Sentinel Desk."

### Scene 1 — Architecture & least privilege  · ~0:30–1:15
**On screen:** README architecture diagram, then briefly `binance_mcp/server.py` and `agents/toolsets.py`.

> "Sentinel Desk is a multi-agent trading desk built on Google's Agent Development Kit. Like a real desk, it separates duties. A Market Analyst researches live Binance data. A Risk Manager vets and sizes the trade. An Execution Trader is the only agent allowed to place orders. A Desk Lead coordinates them. Every agent reaches Binance through one MCP server, and each agent only sees the tools its role needs — the analyst literally has no trade tool. The security lives in code, at the tool boundary, not in a prompt."

### Scene 2 — A simple question  · ~1:15–1:45
**On screen:** terminal — `demo.sh` Scene 1.
**Command:** `trading-agent "What is the current price of BTCUSDT?"`

> "Let's run it. I'll ask for a price. The Desk Lead delegates to the Market Analyst, which calls the get-price tool on the MCP server, and answers with live data. Notice it routed to the right specialist on its own."

### Scene 3 — A full, guarded trade  · ~1:45–2:45
**On screen:** terminal — `demo.sh` Scene 2 (pipeline).
**Command:** `trading-agent --mode pipeline "Evaluate BTCUSDT and buy 0.001 BTC if risk-compliant"`

> "Now a real trade. The analyst reads price, daily stats, and candles, and forms a thesis. The Risk Manager checks the order against hard limits — notional size, open exposure, daily caps — and approves it, item by item. Only then does the Execution Trader place the order, on the Binance testnet. There's the fill: a real order ID, a real quantity. Three specialists, one clean hand-off."

### Scene 4 — The guard blocks bad orders  · ~2:45–3:35
**On screen:** terminal — `demo.sh` Scene 3.

> "But what if an agent goes rogue, or a prompt injection tries to force a bad trade? I'll bypass the agents entirely and call the trade tool directly. First, an order ten times too big — six hundred dollars against a hundred-dollar cap. Rejected, with the exact reason. Now a symbol that isn't on the allow-list. Rejected again. These limits are deterministic Python — the model can reason about risk, but it cannot override it. And rejected orders never even count against the daily budget."

### Scene 5 — Tamper-evident audit  · ~3:35–4:10
**On screen:** terminal — `demo.sh` Scene 4.

> "Every decision and every fill is written to an append-only audit log, chained together with SHA-256 hashes. If anyone edits a past record, the chain breaks. Here's the verification passing — a log you can actually prove wasn't tampered with."

### Scene 6 — Deploy & close  · ~4:10–4:45
**On screen:** browser at `localhost:8000` (ADK web UI), then the green GitHub Actions CI/CD checks and the GHCR package.

> "It's built to ship. One `docker compose up` serves the agent UI in the browser. Continuous integration runs the tests and builds the image; continuous deployment publishes it to the container registry on every merge. Multi-agent orchestration, an MCP server, a real security layer, and a deployment pipeline — Sentinel Desk. Thanks for watching."

---

**Word count ≈ 480 → ~3:50 spoken, leaving headroom under 5:00 for pauses and on-screen reading.**
