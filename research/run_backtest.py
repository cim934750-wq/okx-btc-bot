from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from research.config import BacktestConfig, Paths, StrategyParams
from research.data import load_ohlcv_csv
from research.strategy import extract_metrics, run_backtest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BTC multi-timeframe backtest.")
    parser.add_argument("--csv", required=True, help="Path to 4H OHLCV CSV.")
    parser.add_argument("--save-prefix", default="btc_4h_run", help="Output file prefix.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = Paths()
    df = load_ohlcv_csv(args.csv)
    params = StrategyParams()
    bt_config = BacktestConfig()

    stats, trades = run_backtest(df, params, bt_config)
    metrics = extract_metrics(stats, trades)

    print("Backtest Metrics")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    prefix = paths.output_dir / args.save_prefix
    trades.to_csv(prefix.with_suffix(".trades.csv"), index=False)

    equity = stats["_equity_curve"].copy()
    equity.to_csv(prefix.with_suffix(".equity.csv"), index=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    equity["Equity"].plot(ax=ax, title="Equity Curve")
    ax.set_ylabel("Equity")
    fig.tight_layout()
    fig.savefig(prefix.with_suffix(".equity.png"), dpi=150)


if __name__ == "__main__":
    main()
