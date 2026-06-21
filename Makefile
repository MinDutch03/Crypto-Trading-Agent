.PHONY: help install test lint mcp web run docker-build docker-up docker-down

help:
	@echo "Targets:"
	@echo "  install      Create venv deps (editable install + dev tools)"
	@echo "  test         Run the test suite"
	@echo "  lint         Run ruff"
	@echo "  mcp          Run the Binance MCP server (stdio)"
	@echo "  web          Run the ADK web dev UI on :8000"
	@echo "  run PROMPT=  Run the desk on a prompt (e.g. make run PROMPT='price of BTCUSDT')"
	@echo "  docker-build Build the Docker image"
	@echo "  docker-up    docker compose up (ADK web UI on :8000)"
	@echo "  docker-down  docker compose down"

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests

mcp:
	python -m trading_agent.binance_mcp.server

web:
	adk web adk_agents --host 0.0.0.0 --port 8000

run:
	trading-agent "$(PROMPT)"

docker-build:
	docker compose build

docker-up:
	docker compose up

docker-down:
	docker compose down
