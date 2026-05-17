from __future__ import annotations

import argparse

import pandas as pd

from research.config import Paths
from research.data import load_ohlcv_csv
from research.long_only_candidate import (
    DATE_SPLITS,
    long_only_backtest_config,
    long_only_production_params,
    long_only_production_params_with_fix,
)
from research.strategy import extract_metrics, run_backtest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate long-only production candidate on date splits.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_candidate")
    parser.add_argument("--with-fix", action="store_true")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if start is None and end is None:
        return df
    out = df.copy()
    if start is not None:
        out = out[out.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out[out.index <= pd.Timestamp(end, tz="UTC")]
    return out


def main() -> None:
    args = parse_args()
    paths = Paths()
    df = load_ohlcv_csv(args.csv)
    params = long_only_production_params_with_fix() if args.with_fix else long_only_production_params()
    bt_config = long_only_backtest_config()

    rows = []
    for segment_name, start, end in DATE_SPLITS:
        sliced = slice_frame(df, start, end)
        stats, trades = run_backtest(sliced, params, bt_config)
        metrics = extract_metrics(stats, trades)
        rows.append({"segment": segment_name, **metrics})

    out = pd.DataFrame(rows)
    out_path = paths.output_dir / f"{args.prefix}.validation.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved {out_path}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
