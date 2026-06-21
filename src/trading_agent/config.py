"""Central configuration.

All settings are loaded from environment variables (see `.env.example`) via
pydantic-settings, which gives us validation and typed access. Secrets are read
here and nowhere else, so there is a single audited surface for credentials.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM ---
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    adk_model: str = Field(default="gemini-2.5-flash", alias="ADK_MODEL")

    # --- Binance testnet (order placement) ---
    binance_testnet_api_key: str = Field(default="", alias="BINANCE_TESTNET_API_KEY")
    binance_testnet_api_secret: str = Field(default="", alias="BINANCE_TESTNET_API_SECRET")

    # --- Binance live (read-only market data) ---
    binance_live_api_key: str = Field(default="", alias="BINANCE_LIVE_API_KEY")
    binance_live_api_secret: str = Field(default="", alias="BINANCE_LIVE_API_SECRET")

    # --- Risk limits ---
    risk_max_notional_usdt: float = Field(default=100.0, alias="RISK_MAX_NOTIONAL_USDT")
    risk_max_open_notional_usdt: float = Field(default=500.0, alias="RISK_MAX_OPEN_NOTIONAL_USDT")
    risk_max_daily_loss_usdt: float = Field(default=50.0, alias="RISK_MAX_DAILY_LOSS_USDT")
    risk_allowed_symbols: str = Field(default="BTCUSDT,ETHUSDT", alias="RISK_ALLOWED_SYMBOLS")
    risk_max_orders_per_day: int = Field(default=25, alias="RISK_MAX_ORDERS_PER_DAY")
    trading_enabled: bool = Field(default=True, alias="TRADING_ENABLED")

    # --- Audit ---
    audit_log_path: str = Field(default="audit/trades.jsonl", alias="AUDIT_LOG_PATH")

    @field_validator("risk_allowed_symbols")
    @classmethod
    def _strip_symbols(cls, v: str) -> str:
        return ",".join(s.strip().upper() for s in v.split(",") if s.strip())

    @property
    def allowed_symbols(self) -> set[str]:
        return {s for s in self.risk_allowed_symbols.split(",") if s}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read env once per process)."""
    return Settings()
