from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import configure_logging, load_config
from src.data import fetch_ohlcv_dataframe
from src.exchange import OKXExchangeClient
from src.strategy import add_signal_columns


def run_backtest(df: pd.DataFrame, fee_rate: float, slippage_rate: float) -> dict[str, float]:
    data = add_signal_columns(df).dropna().copy()
    if data.empty:
        return {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "number_of_trades": 0,
        }

    in_position = False
    position = []
    trades = []
    entry_price = 0.0

    for _, row in data.iterrows():
        if not in_position and bool(row["long_entry"]):
            in_position = True
            entry_price = float(row["close"]) * (1 + slippage_rate)
            position.append(1)
            continue

        if in_position and bool(row["exit"]):
            exit_price = float(row["close"]) * (1 - slippage_rate)
            gross_return = (exit_price - entry_price) / entry_price
            net_return = gross_return - (2 * fee_rate)
            trades.append(net_return)
            in_position = False
            entry_price = 0.0
            position.append(0)
            continue

        position.append(1 if in_position else 0)

    data["position"] = position
    data["returns"] = data["close"].pct_change().fillna(0.0)
    data["strategy_returns"] = data["position"].shift(1).fillna(0.0) * data["returns"]
    data["turnover"] = data["position"].diff().abs().fillna(data["position"].abs())
    data["costs"] = data["turnover"] * (fee_rate + slippage_rate)
    data["strategy_returns"] = data["strategy_returns"] - data["costs"]
    data["equity_curve"] = (1 + data["strategy_returns"]).cumprod()

    total_return = float(data["equity_curve"].iloc[-1] - 1)
    running_max = data["equity_curve"].cummax()
    drawdown = data["equity_curve"] / running_max - 1
    max_drawdown = float(drawdown.min())

    wins = [trade for trade in trades if trade > 0]
    losses = [trade for trade in trades if trade < 0]
    win_rate = len(wins) / len(trades) if trades else 0.0
    profit_factor = (
        sum(wins) / abs(sum(losses))
        if losses
        else float("inf")
        if wins
        else 0.0
    )

    return {
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "profit_factor": float(profit_factor),
        "number_of_trades": len(trades),
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
