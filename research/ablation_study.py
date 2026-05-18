from __future__ import annotations

import argparse
from dataclasses import asdict, replace

import pandas as pd

from research.config import BacktestConfig, Paths, StrategyParams
from research.data import load_ohlcv_csv
from research.strategy import extract_metrics, run_backtest


DATE_SPLITS = [
    ("full_sample", None, None),
    ("2019_2022", "2019-01-01", "2022-12-31 23:59:59"),
    ("2023_2024", "2023-01-01", "2024-12-31 23:59:59"),
    ("2025_2026", "2025-01-01", "2026-04-12 23:59:59"),
]


VARIANTS = {
    "long_only": BacktestConfig(allow_longs=True, allow_shorts=False, enable_add_on_entries=True),
    "short_only": BacktestConfig(allow_longs=False, allow_shorts=True, enable_add_on_entries=True),
    "long_only_no_addons": BacktestConfig(allow_longs=True, allow_shorts=False, enable_add_on_entries=False, add_on_size=0.0),
    "short_only_no_addons": BacktestConfig(allow_longs=False, allow_shorts=True, enable_add_on_entries=False, add_on_size=0.0),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run long/short/add-on ablation study.")
    parser.add_argument("--csv", required=True, help="Path to 4H OHLCV CSV.")
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
    params = StrategyParams()

    split_rows: list[dict] = []
    summary_rows: list[dict] = []

    for variant_name, bt_config in VARIANTS.items():
        full_metrics = None
        for segment_name, start, end in DATE_SPLITS:
            sliced = slice_frame(df, start, end)
            stats, trades = run_backtest(sliced, params, bt_config)
            metrics = extract_metrics(stats, trades)
            row = {
                "variant": variant_name,
                "segment": segment_name,
                **metrics,
                "allow_longs": bt_config.allow_longs,
                "allow_shorts": bt_config.allow_shorts,
                "enable_add_on_entries": bt_config.enable_add_on_entries,
            }
            split_rows.append(row)
            if segment_name == "full_sample":
                full_metrics = row

        split_df_one = pd.DataFrame([r for r in split_rows if r["variant"] == variant_name])
        oos = split_df_one[split_df_one["segment"] != "full_sample"]
        survives = (
            full_metrics["profit_factor"] >= 1.15
            and full_metrics["avg_trade"] > 0
            and full_metrics["max_drawdown_pct"] <= 25
            and full_metrics["total_trades"] >= 35
            and (oos["profit_factor"] >= 0.9).all()
            and (oos["avg_trade"] > 0).all()
            and (oos["max_drawdown_pct"] <= 25).all()
        )
        summary_rows.append(
            {
                "variant": variant_name,
                "survives_validation": survives,
                **full_metrics,
            }
        )

    by_split_df = pd.DataFrame(split_rows)
    full_df = by_split_df[by_split_df["segment"] == "full_sample"].copy()
    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["survives_validation", "profit_factor", "expectancy", "net_profit"],
        ascending=[False, False, False, False],
    )

    full_path = paths.output_dir / "ablation_full_sample.csv"
    split_path = paths.output_dir / "ablation_by_split.csv"
    summary_path = paths.output_dir / "ablation_summary.csv"

    full_df.to_csv(full_path, index=False)
    by_split_df.to_csv(split_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Saved {full_path}")
    print(f"Saved {split_path}")
    print(f"Saved {summary_path}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
