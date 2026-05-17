from __future__ import annotations

import argparse
from dataclasses import asdict

import pandas as pd

from research.config import Paths
from research.data import load_ohlcv_csv
from research.long_only_candidate import (
    long_only_backtest_config,
    long_only_split_leg_experiment_params,
)
from research.strategy import extract_metrics, run_backtest


TEST_MATRIX = [
    {"case": "case1", "long_tp1_leg_fraction": 0.50, "tp1_rr": 1.00, "long_tp2_trail_atr_mult": 0.00},
    {"case": "case2", "long_tp1_leg_fraction": 0.33, "tp1_rr": 1.00, "long_tp2_trail_atr_mult": 0.00},
    {"case": "case3", "long_tp1_leg_fraction": 0.25, "tp1_rr": 1.00, "long_tp2_trail_atr_mult": 0.00},
    {"case": "case4", "long_tp1_leg_fraction": 0.33, "tp1_rr": 1.20, "long_tp2_trail_atr_mult": 0.00},
    {"case": "case5", "long_tp1_leg_fraction": 0.33, "tp1_rr": 1.20, "long_tp2_trail_atr_mult": 2.00},
]

BASELINE_FULL_SAMPLE = {
    "net_profit": 1207.61,
    "profit_factor": 2.09,
    "lifecycle_avg_pnl": 13.72,
}
BASELINE_2025_2026_LIFECYCLE_NET = -5.931829400913557


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a narrow split-leg mini experiment.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="split_leg_mini")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    out = df.copy()
    if start is not None:
        out = out[out.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        out = out[out.index <= pd.Timestamp(end, tz="UTC")]
    return out


def lifecycle_metrics(trades: pd.DataFrame) -> dict[str, float]:
    if trades.empty:
        return {
            "lifecycle_count": 0.0,
            "lifecycle_net_profit": 0.0,
            "lifecycle_pf": 0.0,
            "lifecycle_avg_pnl": 0.0,
            "lifecycle_win_rate": 0.0,
        }

    grouped = (
        trades.groupby("EntryTime", as_index=False)
        .agg(
            lifecycle_pnl=("PnL", "sum"),
            leg_count=("Tag", "count"),
        )
        .copy()
    )
    pnl = grouped["lifecycle_pnl"].astype(float)
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = -pnl[pnl < 0].sum()
    lifecycle_pf = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0
    return {
        "lifecycle_count": float(len(grouped)),
        "lifecycle_net_profit": float(pnl.sum()),
        "lifecycle_pf": float(lifecycle_pf),
        "lifecycle_avg_pnl": float(pnl.mean()),
        "lifecycle_win_rate": float((pnl > 0).mean() * 100.0),
    }


def acceptance_rule(full_row: dict, weak_row: dict) -> tuple[bool, str]:
    full_ok = (
        full_row["lifecycle_pf"] >= 1.60
        and full_row["lifecycle_avg_pnl"] >= 8.0
        and full_row["net_profit"] >= 700.0
    )
    weak_ok = (
        (weak_row["lifecycle_net_profit"] - BASELINE_2025_2026_LIFECYCLE_NET) >= 25.0
        or weak_row["lifecycle_pf"] >= 1.15
    )

    if full_ok and weak_ok:
        return True, "alive"
    if weak_ok and not full_ok:
        return False, "weak_segment_improved_but_full_sample_failed"
    return False, "rejected"


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    bt_config = long_only_backtest_config()

    segment_map = {
        "full_sample": (None, None),
        "2025_2026": ("2025-01-01", "2026-04-12 23:59:59"),
    }

    detail_rows: list[dict] = []
    summary_rows: list[dict] = []

    for case in TEST_MATRIX:
        params = long_only_split_leg_experiment_params(
            long_tp1_leg_fraction=case["long_tp1_leg_fraction"],
            tp1_rr=case["tp1_rr"],
            long_tp2_trail_atr_mult=case["long_tp2_trail_atr_mult"],
        )
        case_results: dict[str, dict] = {}

        for segment_name, (start, end) in segment_map.items():
            sliced = slice_frame(raw_df, start, end)
            stats, trades = run_backtest(sliced, params, bt_config)
            raw_metrics = extract_metrics(stats, trades)
            life_metrics = lifecycle_metrics(trades)
            row = {
                "case": case["case"],
                "segment": segment_name,
                **case,
                **raw_metrics,
                **life_metrics,
            }
            detail_rows.append(row)
            case_results[segment_name] = row

        accepted, status = acceptance_rule(case_results["full_sample"], case_results["2025_2026"])
        summary_rows.append(
            {
                **case,
                "full_sample_net_profit": case_results["full_sample"]["net_profit"],
                "full_sample_profit_factor": case_results["full_sample"]["profit_factor"],
                "full_sample_lifecycle_pf": case_results["full_sample"]["lifecycle_pf"],
                "full_sample_lifecycle_avg_pnl": case_results["full_sample"]["lifecycle_avg_pnl"],
                "full_sample_lifecycle_count": case_results["full_sample"]["lifecycle_count"],
                "weak_2025_2026_net_profit": case_results["2025_2026"]["net_profit"],
                "weak_2025_2026_profit_factor": case_results["2025_2026"]["profit_factor"],
                "weak_2025_2026_lifecycle_net_profit": case_results["2025_2026"]["lifecycle_net_profit"],
                "weak_2025_2026_lifecycle_pf": case_results["2025_2026"]["lifecycle_pf"],
                "weak_2025_2026_lifecycle_avg_pnl": case_results["2025_2026"]["lifecycle_avg_pnl"],
                "weak_2025_2026_lifecycle_count": case_results["2025_2026"]["lifecycle_count"],
                "accepted": accepted,
                "status": status,
            }
        )

    details_df = pd.DataFrame(detail_rows).sort_values(["case", "segment"])
    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["accepted", "full_sample_lifecycle_pf", "weak_2025_2026_lifecycle_pf"],
        ascending=[False, False, False],
    )

    detail_path = paths.output_dir / f"{args.prefix}.detail.csv"
    summary_path = paths.output_dir / f"{args.prefix}.summary.csv"

    details_df.to_csv(detail_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Saved {detail_path}")
    print(f"Saved {summary_path}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
