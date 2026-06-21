# syntax=docker/dockerfile:1
# Python 3.12 (stable wheels) — the app supports >=3.11.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install the application.
COPY src ./src
COPY adk_agents ./adk_agents
RUN pip install --no-cache-dir -e .

# Run as a non-root user.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Default: serve the ADK web dev UI for the desk.
CMD ["adk", "web", "adk_agents", "--host", "0.0.0.0", "--port", "8000"]
