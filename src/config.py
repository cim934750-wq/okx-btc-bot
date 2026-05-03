from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parse_bool(value: Optional[str], default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a float, got {raw!r}") from exc


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


@dataclass(frozen=True)
class BotConfig:
    okx_api_key: str
    okx_secret_key: str
    okx_passphrase: str
    okx_demo: bool
    okx_demo_raw: Optional[str]
    dry_run: bool
    dry_run_raw: Optional[str]
    symbol: str
    timeframe: str
    strategy_variant: str
    atr_percentile_window: int
    ema200_slope_lookback: int
    loop_interval_seconds: int
    max_risk_per_trade: float
    max_daily_loss: float
    max_monthly_loss: float
    kill_switch: bool
    log_level: str
    bot_mode: str
    candle_limit: int
    paper_starting_equity: float
    atr_stop_multiplier: float
    fee_rate: float
    slippage_rate: float
    error_threshold: int
    cooldown_seconds: int
    allow_repeat_candle_actions: bool
    logs_dir: Path
    data_dir: Path
    runtime_dir: Path
    default_order_type: str
    okx_default_type: str

    @property
    def api_keys_available(self) -> bool:
        return bool(self.okx_api_key and self.okx_secret_key and self.okx_passphrase)

    @property
    def paper_state_path(self) -> Path:
        return self.data_dir / "paper_state.json"

    @property
    def trades_log_path(self) -> Path:
        return self.logs_dir / "trades.csv"

    @property
    def heartbeat_log_path(self) -> Path:
        return self.logs_dir / "heartbeat.csv"

    def ensure_directories(self) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> BotConfig:
    load_dotenv(PROJECT_ROOT / ".env")

    config = BotConfig(
        okx_api_key=os.getenv("OKX_API_KEY", ""),
        okx_secret_key=os.getenv("OKX_SECRET_KEY", ""),
        okx_passphrase=os.getenv("OKX_PASSPHRASE", ""),
        okx_demo=_parse_bool(os.getenv("OKX_DEMO"), True),
        okx_demo_raw=os.getenv("OKX_DEMO"),
        dry_run=_parse_bool(os.getenv("DRY_RUN"), True),
        dry_run_raw=os.getenv("DRY_RUN"),
        symbol=os.getenv("SYMBOL", "BTC/USDT"),
        timeframe=os.getenv("TIMEFRAME", "1h"),
        strategy_variant=os.getenv("STRATEGY_VARIANT", "baseline").strip().lower(),
        atr_percentile_window=_get_int("ATR_PERCENTILE_WINDOW", 200),
        ema200_slope_lookback=_get_int("EMA200_SLOPE_LOOKBACK", 12),
        loop_interval_seconds=_get_int("LOOP_INTERVAL_SECONDS", 60),
        max_risk_per_trade=_get_float("MAX_RISK_PER_TRADE", 0.005),
        max_daily_loss=_get_float("MAX_DAILY_LOSS", 0.02),
        max_monthly_loss=_get_float("MAX_MONTHLY_LOSS", 0.10),
        kill_switch=_parse_bool(os.getenv("KILL_SWITCH"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        bot_mode=os.getenv("BOT_MODE", "live_loop").lower(),
        candle_limit=_get_int("CANDLE_LIMIT", 300),
        paper_starting_equity=_get_float("PAPER_STARTING_EQUITY", 10_000.0),
        atr_stop_multiplier=_get_float("ATR_STOP_MULTIPLIER", 2.0),
        fee_rate=_get_float("FEE_RATE", 0.001),
        slippage_rate=_get_float("SLIPPAGE_RATE", 0.0005),
        error_threshold=_get_int("ERROR_THRESHOLD", 5),
        cooldown_seconds=_get_int("COOLDOWN_SECONDS", 300),
        allow_repeat_candle_actions=_parse_bool(
            os.getenv("ALLOW_REPEAT_CANDLE_ACTIONS"), False
        ),
        logs_dir=PROJECT_ROOT / os.getenv("LOGS_DIR", "logs"),
        data_dir=PROJECT_ROOT / os.getenv("DATA_DIR", "data"),
        runtime_dir=PROJECT_ROOT / os.getenv("RUNTIME_DIR", "runtime"),
        default_order_type=os.getenv("DEFAULT_ORDER_TYPE", "market"),
        okx_default_type=os.getenv("OKX_DEFAULT_TYPE", "spot"),
    )

    validate_config(config)
    return config


def validate_config(config: BotConfig) -> None:
    if config.loop_interval_seconds < 1:
        raise ValueError("LOOP_INTERVAL_SECONDS must be at least 1")
    if not 0 < config.max_risk_per_trade <= 0.05:
        raise ValueError("MAX_RISK_PER_TRADE must be greater than 0 and <= 0.05")
    if not 0 < config.max_daily_loss <= 1:
        raise ValueError("MAX_DAILY_LOSS must be greater than 0 and <= 1")
    if not 0 < config.max_monthly_loss <= 1:
        raise ValueError("MAX_MONTHLY_LOSS must be greater than 0 and <= 1")
    if config.paper_starting_equity <= 0:
        raise ValueError("PAPER_STARTING_EQUITY must be greater than 0")

    if config.dry_run:
        return

    if config.dry_run_raw != "0":
        raise ValueError("Real trading refused: DRY_RUN must be explicitly set to 0")
    if config.okx_demo_raw not in {"0", "1"}:
        raise ValueError("Real trading refused: OKX_DEMO must be explicitly set to 0 or 1")
    if config.kill_switch:
        raise ValueError("Real trading refused: KILL_SWITCH is active")
    if not config.api_keys_available:
        raise ValueError("Real trading refused: OKX API key, secret, and passphrase are required")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
