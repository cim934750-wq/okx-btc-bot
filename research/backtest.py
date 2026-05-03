from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.compare_strategy_variants import (
    SimulationConfig,
    Variant,
    parse_float_env,
    prepare_data,
    simulate_variant,
)
from src.config import configure_logging, load_config
from src.data import fetch_ohlcv_dataframe
from src.exchange import OKXExchangeClient


def run_backtest(df: pd.DataFrame, fee_rate: float, slippage_rate: float) -> dict[str, float]:
    data = prepare_data(df)
    if data.empty:
        return {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "number_of_trades": 0,
        }

    load_dotenv(ROOT / ".env")
    simulation_config = SimulationConfig(
        starting_equity=parse_float_env("PAPER_STARTING_EQUITY", 10_000.0),
        fee_rate=fee_rate,
        slippage_rate_config=slippage_rate,
        max_risk_per_trade=parse_float_env("MAX_RISK_PER_TRADE", 0.005),
        atr_stop_multiplier=parse_float_env("ATR_STOP_MULTIPLIER", 2.0),
        max_daily_loss=parse_float_env("MAX_DAILY_LOSS", 0.02),
        max_monthly_loss=parse_float_env("MAX_MONTHLY_LOSS", 0.10),
    )
    metrics = simulate_variant(
        data,
        Variant("Baseline", "Paper-compatible baseline strategy backtest."),
        simulation_config,
    )

    return {
        "total_return": metrics.total_return,
        "max_drawdown": metrics.max_drawdown,
        "win_rate": metrics.win_rate,
        "profit_factor": float(metrics.profit_factor or 0.0),
        "number_of_trades": metrics.number_of_trades,
    }


def main() -> None:
    config = load_config()
    configure_logging(config.log_level)
    exchange_client = OKXExchangeClient(config)
    df = fetch_ohlcv_dataframe(
        exchange_client,
        symbol=config.symbol,
        timeframe=config.timeframe,
        limit=config.candle_limit,
    )
    metrics = run_backtest(df, fee_rate=config.fee_rate, slippage_rate=config.slippage_rate)
    print("Backtest metrics")
    for key, value in metrics.items():
        print(f"{key}: {value:.6f}" if isinstance(value, float) else f"{key}: {value}")


if __name__ == "__main__":
    main()
