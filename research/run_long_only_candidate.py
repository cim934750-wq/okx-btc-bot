from __future__ import annotations

import argparse

import matplotlib.pyplot as plt

from research.config import Paths
from research.data import load_ohlcv_csv
from research.long_only_candidate import (
    long_only_backtest_config,
    long_only_production_params,
    long_only_production_params_with_fix,
)
from research.strategy import extract_metrics, run_backtest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run long-only production candidate backtest.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--save-prefix", default="long_only_candidate")
    parser.add_argument("--with-fix", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = Paths()
    df = load_ohlcv_csv(args.csv)
    params = long_only_production_params_with_fix() if args.with_fix else long_only_production_params()
    bt_config = long_only_backtest_config()

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
    equity["Equity"].plot(ax=ax, title="Long-Only Candidate Equity Curve")
    ax.set_ylabel("Equity")
    fig.tight_layout()
    fig.savefig(prefix.with_suffix(".equity.png"), dpi=150)


if __name__ == "__main__":
    main()
