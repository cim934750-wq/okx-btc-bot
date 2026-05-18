from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from pathlib import Path

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate top candidate parameter sets on full sample and date splits.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--top", type=int, default=5)
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


def row_to_params(row: pd.Series) -> StrategyParams:
    base = asdict(StrategyParams())
    for key in base:
        if key in row and pd.notna(row[key]):
            base[key] = row[key]
    return StrategyParams(**base)


def candidate_rows(paths: Paths, top_n: int) -> pd.DataFrame:
    phase1 = pd.read_csv(paths.output_dir / "phase1_entry_frequency_btc4h.top_trials.csv").head(top_n)
    phase2 = pd.read_csv(paths.output_dir / "phase2_directional_quality_btc4h.top_trials.csv").head(top_n)
    phase3 = pd.read_csv(paths.output_dir / "phase3_trade_management_btc4h.top_trials.csv").head(top_n)

    baseline = pd.DataFrame([asdict(StrategyParams())])
    baseline["source"] = "locked_baseline"
    baseline["candidate_id"] = "baseline"

    frames = []
    for name, frame in [("phase1", phase1), ("phase2", phase2), ("phase3", phase3)]:
        frame = frame.copy()
        frame["source"] = name
        frame["candidate_id"] = [f"{name}_{i}" for i in range(len(frame))]
        frames.append(frame)

    combined = pd.concat([baseline, *frames], ignore_index=True, sort=False)
    subset_cols = [
        "min_exec_adx",
        "min_exec_atr_ratio",
        "min_ema_distance_atr",
        "pullback_overshoot_atr",
        "cooldown_bars",
        "direction_cooldown_bars",
        "long_rsi_min",
        "short_rsi_max",
        "stop_atr_mult",
        "tp2_rr",
        "trail_atr_mult",
        "add_on_profit_atr",
    ]
    combined = combined.drop_duplicates(subset=subset_cols).reset_index(drop=True)
    return combined


def is_rejected(full_row: pd.Series, split_rows: pd.DataFrame) -> tuple[bool, str]:
    if full_row["total_trades"] < 35:
        return True, "full_sample_trades_lt_35"
    if full_row["profit_factor"] < 1.15:
        return True, "full_sample_pf_lt_1.15"
    if full_row["avg_trade"] <= 0:
        return True, "full_sample_avg_trade_le_0"
    if full_row["max_drawdown_pct"] > 25:
        return True, "full_sample_dd_gt_25"

    non_full = split_rows[split_rows["segment"] != "full_sample"].copy()
    if not non_full.empty:
        pf_min = float(non_full["profit_factor"].min())
        pf_max = float(non_full["profit_factor"].max())
        exp_min = float(non_full["expectancy"].min())
        exp_max = float(non_full["expectancy"].max())
        if pf_min < 0.9 or exp_min <= 0:
            return True, "oos_segment_collapse"
        if pf_max > 0 and pf_min / pf_max < 0.55:
            return True, "oos_pf_instability"
        if exp_max > 0 and exp_min / exp_max < 0.35:
            return True, "oos_expectancy_instability"

    for _, row in split_rows.iterrows():
        if row["segment"] == "full_sample":
            continue
        if row["profit_factor"] < 0.9 or row["avg_trade"] <= 0:
            return True, f"{row['segment']}_collapse"
        if row["max_drawdown_pct"] > 25:
            return True, f"{row['segment']}_dd_gt_25"
    return False, ""


def main() -> None:
    args = parse_args()
    paths = Paths()
    df = load_ohlcv_csv(args.csv)
    bt_config = BacktestConfig()

    candidates = candidate_rows(paths, args.top)
    summary_rows: list[dict] = []
    split_rows: list[dict] = []

    for _, candidate in candidates.iterrows():
        params = row_to_params(candidate)
        full_metrics: dict | None = None
        per_candidate_rows: list[dict] = []

        for segment_name, start, end in DATE_SPLITS:
            sliced = slice_frame(df, start, end)
            stats, trades = run_backtest(sliced, params, bt_config)
            metrics = extract_metrics(stats, trades)
            metrics["segment"] = segment_name
            metrics["candidate_id"] = candidate["candidate_id"]
            metrics["source"] = candidate["source"]
            metrics.update(asdict(params))
            split_rows.append(metrics)
            per_candidate_rows.append(metrics)
            if segment_name == "full_sample":
                full_metrics = metrics

        full_row = pd.Series(full_metrics)
        split_df = pd.DataFrame(per_candidate_rows)
        rejected, reason = is_rejected(full_row, split_df)

        summary_rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "source": candidate["source"],
                "rejected": rejected,
                "reject_reason": reason,
                "net_profit": full_row["net_profit"],
                "profit_factor": full_row["profit_factor"],
                "max_drawdown_pct": full_row["max_drawdown_pct"],
                "total_trades": full_row["total_trades"],
                "percent_profitable": full_row["percent_profitable"],
                "avg_trade": full_row["avg_trade"],
                "expectancy": full_row["expectancy"],
                **asdict(params),
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["rejected", "profit_factor", "expectancy", "net_profit"],
        ascending=[True, False, False, False],
    )
    split_df = pd.DataFrame(split_rows).sort_values(["candidate_id", "segment"])
    survivors_df = summary_df[summary_df["rejected"] == False].copy()

    summary_path = paths.output_dir / "candidate_validation_full_sample.csv"
    split_path = paths.output_dir / "candidate_validation_by_split.csv"
    survivors_path = paths.output_dir / "candidate_validation_survivors.csv"
    summary_df.to_csv(summary_path, index=False)
    split_df.to_csv(split_path, index=False)
    survivors_df.to_csv(survivors_path, index=False)

    print(f"Saved {summary_path}")
    print(f"Saved {split_path}")
    print(f"Saved {survivors_path}")
    if not survivors_df.empty:
        print("Top survivors:")
        print(
            survivors_df[
                [
                    "candidate_id",
                    "source",
                    "net_profit",
                    "profit_factor",
                    "max_drawdown_pct",
                    "total_trades",
                    "avg_trade",
                    "expectancy",
                ]
            ]
            .head(10)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
