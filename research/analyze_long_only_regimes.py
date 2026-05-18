from __future__ import annotations

import argparse

import pandas as pd

from research.config import Paths
from research.data import load_ohlcv_csv
from research.indicators import build_feature_frame
from research.long_only_candidate import long_only_backtest_config, long_only_production_params
from research.strategy import run_backtest


WEAK_START = pd.Timestamp("2025-01-01", tz="UTC")
WEAK_END = pd.Timestamp("2026-04-12 23:59:59", tz="UTC")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose regime distribution for baseline long-only trades.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_regime_diagnostic")
    return parser.parse_args()


def classify_regime_strength(summary: pd.DataFrame) -> str:
    if summary.empty:
        return "no_evidence"
    strong = summary[
        (summary["weak_loser_count"] >= 2)
        & (summary["weak_loser_share"] >= 0.5)
        & ((summary["weak_loser_share"] - summary["historical_winner_share"]) >= 0.2)
    ]
    if not strong.empty:
        return "strong_enough_regime_concentration"
    return "no_strong_regime_concentration"


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    params = long_only_production_params()
    bt_config = long_only_backtest_config()

    stats, trades = run_backtest(raw_df, params, bt_config)
    frame = build_feature_frame(raw_df, params)
    trades = trades.copy()
    trades["EntryTime"] = pd.to_datetime(trades["EntryTime"], utc=True)
    trades["ExitTime"] = pd.to_datetime(trades["ExitTime"], utc=True)

    entry_lookup = frame.reset_index().rename(columns={"index": "timestamp"})
    entry_cols = [
        "timestamp",
        "regime_label",
        "weekly_bull",
        "daily_bull",
        "exec_bull_structure",
        "exec_slope_up",
        "adx",
        "atr_ratio",
        "exec_distance_atr",
        "close_ema20_gap_atr",
        "rsi",
        "di_spread",
    ]
    enriched = trades.merge(entry_lookup[entry_cols], left_on="EntryTime", right_on="timestamp", how="left")
    enriched = enriched.drop(columns=["timestamp"])
    enriched["is_weak_slice"] = (enriched["EntryTime"] >= WEAK_START) & (enriched["EntryTime"] <= WEAK_END)
    enriched["is_winner"] = enriched["PnL"] > 0
    enriched["is_loser"] = enriched["PnL"] <= 0

    weak_losers = enriched[enriched["is_weak_slice"] & enriched["is_loser"]].copy()
    historical_winners = enriched[enriched["is_winner"]].copy()

    all_dist = (
        enriched.groupby("regime_label", dropna=False)
        .agg(trade_count=("PnL", "size"), net_pnl=("PnL", "sum"), avg_trade=("PnL", "mean"))
        .reset_index()
        .sort_values(["trade_count", "net_pnl"], ascending=[False, False])
    )
    weak_dist = (
        weak_losers.groupby("regime_label", dropna=False)
        .agg(weak_loser_count=("PnL", "size"), weak_loser_pnl=("PnL", "sum"))
        .reset_index()
    )
    winner_dist = (
        historical_winners.groupby("regime_label", dropna=False)
        .agg(historical_winner_count=("PnL", "size"), historical_winner_pnl=("PnL", "sum"))
        .reset_index()
    )

    summary = all_dist.merge(weak_dist, on="regime_label", how="left").merge(winner_dist, on="regime_label", how="left")
    fill_cols = [
        "weak_loser_count",
        "weak_loser_pnl",
        "historical_winner_count",
        "historical_winner_pnl",
    ]
    summary[fill_cols] = summary[fill_cols].fillna(0.0)
    total_weak_losers = max(float(len(weak_losers)), 1.0)
    total_winners = max(float(len(historical_winners)), 1.0)
    summary["weak_loser_share"] = summary["weak_loser_count"] / total_weak_losers
    summary["historical_winner_share"] = summary["historical_winner_count"] / total_winners
    summary["share_gap_vs_winners"] = summary["weak_loser_share"] - summary["historical_winner_share"]
    summary = summary.sort_values(
        ["weak_loser_share", "share_gap_vs_winners", "trade_count"],
        ascending=[False, False, False],
    )

    recommendation = classify_regime_strength(summary)
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": recommendation,
                "weak_loser_count": len(weak_losers),
                "historical_winner_count": len(historical_winners),
                "top_regime": summary.iloc[0]["regime_label"] if not summary.empty else "none",
                "top_regime_weak_loser_share": summary.iloc[0]["weak_loser_share"] if not summary.empty else 0.0,
                "top_regime_winner_share": summary.iloc[0]["historical_winner_share"] if not summary.empty else 0.0,
            }
        ]
    )

    prefix = paths.output_dir / args.prefix
    enriched.to_csv(prefix.with_name(f"{prefix.name}.trade_regimes.csv"), index=False)
    all_dist.to_csv(prefix.with_name(f"{prefix.name}.regime_distribution_all_trades.csv"), index=False)
    weak_dist.to_csv(prefix.with_name(f"{prefix.name}.regime_distribution_2025_2026_losers.csv"), index=False)
    winner_dist.to_csv(prefix.with_name(f"{prefix.name}.regime_distribution_historical_winners.csv"), index=False)
    summary.to_csv(prefix.with_name(f"{prefix.name}.regime_concentration_summary.csv"), index=False)
    recommendation_df.to_csv(prefix.with_name(f"{prefix.name}.recommendation.csv"), index=False)

    print(f"Saved {prefix.with_name(f'{prefix.name}.trade_regimes.csv')}")
    print(f"Saved {prefix.with_name(f'{prefix.name}.regime_concentration_summary.csv')}")
    print(summary.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
 