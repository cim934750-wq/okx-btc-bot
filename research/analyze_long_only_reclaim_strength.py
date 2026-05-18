from __future__ import annotations

import argparse

import pandas as pd

from research.analyze_long_only_reclaim import WEAK_END, WEAK_START, label_trade
from research.config import Paths
from research.data import load_ohlcv_csv
from research.indicators import build_feature_frame
from research.long_only_candidate import long_only_backtest_config, long_only_production_params
from research.strategy import run_backtest


RECENT_START = pd.Timestamp("2023-01-01", tz="UTC")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stress-test strict reclaim/retest labels across broader loser/winner sets.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_reclaim_strength_round1")
    return parser.parse_args()


def summarize_bucket(df: pd.DataFrame, bucket_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            [
                {
                    "bucket": bucket_name,
                    "reclaim_label": "none",
                    "count": 0,
                    "share": 0.0,
                    "win_rate": 0.0,
                    "avg_trade": 0.0,
                    "avg_loss": 0.0,
                    "avg_win": 0.0,
                    "net_pnl": 0.0,
                }
            ]
        )

    rows = []
    total = max(float(len(df)), 1.0)
    for label, grp in df.groupby("reclaim_label", dropna=False):
        pnl = grp["PnL"].astype(float)
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]
        rows.append(
            {
                "bucket": bucket_name,
                "reclaim_label": label,
                "count": len(grp),
                "share": len(grp) / total,
                "win_rate": float((pnl > 0).mean()),
                "avg_trade": float(pnl.mean()),
                "avg_loss": float(losses.mean()) if not losses.empty else 0.0,
                "avg_win": float(wins.mean()) if not wins.empty else 0.0,
                "net_pnl": float(pnl.sum()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    params = long_only_production_params()
    bt_config = long_only_backtest_config()

    _, trades = run_backtest(raw_df, params, bt_config)
    frame = build_feature_frame(raw_df, params)
    labeled = pd.DataFrame([label_trade(frame, trade) for _, trade in trades.iterrows()])

    labeled["is_winner"] = labeled["PnL"] > 0
    labeled["is_loser"] = labeled["PnL"] <= 0
    labeled["is_recent"] = labeled["EntryTime"] >= RECENT_START
    labeled["is_weak_slice"] = (labeled["EntryTime"] >= WEAK_START) & (labeled["EntryTime"] <= WEAK_END)
    labeled["is_small_win"] = (labeled["PnL"] > 0) & (labeled["PnL"] <= labeled["PnL"].median())

    buckets = {
        "all_trades": labeled,
        "full_sample_losers": labeled[labeled["is_loser"]],
        "recent_period_losers": labeled[labeled["is_loser"] & labeled["is_recent"]],
        "weak_slice_losers": labeled[labeled["is_loser"] & labeled["is_weak_slice"]],
        "historical_winners": labeled[labeled["is_winner"]],
        "small_wins": labeled[labeled["is_small_win"]],
    }

    bucket_summaries = pd.concat([summarize_bucket(df, name) for name, df in buckets.items()], ignore_index=True)

    focus = bucket_summaries[bucket_summaries["reclaim_label"] == "reclaim_then_failed_hold"].copy()
    focus_pivot = focus.pivot_table(
        index="reclaim_label",
        columns="bucket",
        values=["share", "win_rate", "avg_trade", "avg_loss", "net_pnl"],
        aggfunc="first",
    )
    focus_pivot.columns = [f"{metric}_{bucket}" for metric, bucket in focus_pivot.columns]
    focus_pivot = focus_pivot.reset_index()

    weak_share = float(
        focus.loc[focus["bucket"] == "weak_slice_losers", "share"].iloc[0]
        if not focus.loc[focus["bucket"] == "weak_slice_losers", "share"].empty
        else 0.0
    )
    full_loser_share = float(
        focus.loc[focus["bucket"] == "full_sample_losers", "share"].iloc[0]
        if not focus.loc[focus["bucket"] == "full_sample_losers", "share"].empty
        else 0.0
    )
    recent_loser_share = float(
        focus.loc[focus["bucket"] == "recent_period_losers", "share"].iloc[0]
        if not focus.loc[focus["bucket"] == "recent_period_losers", "share"].empty
        else 0.0
    )
    winner_share = float(
        focus.loc[focus["bucket"] == "historical_winners", "share"].iloc[0]
        if not focus.loc[focus["bucket"] == "historical_winners", "share"].empty
        else 0.0
    )

    strengthened = (
        weak_share >= 0.5
        and full_loser_share >= 0.2
        and recent_loser_share >= 0.2
        and (min(weak_share, full_loser_share, recent_loser_share) - winner_share) >= 0.1
    )
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": "evidence_strengthened_enough_for_narrow_validation" if strengthened else "evidence_still_too_weak_do_not_patch",
                "weak_slice_share": weak_share,
                "full_sample_loser_share": full_loser_share,
                "recent_period_loser_share": recent_loser_share,
                "historical_winner_share": winner_share,
            }
        ]
    )

    prefix = paths.output_dir / args.prefix
    labeled.to_csv(prefix.with_name(f"{prefix.name}.strict_reclaim_labels_all.csv"), index=False)
    bucket_summaries.to_csv(prefix.with_name(f"{prefix.name}.bucket_summary.csv"), index=False)
    focus_pivot.to_csv(prefix.with_name(f"{prefix.name}.focus_reclaim_then_failed_hold.csv"), index=False)
    recommendation_df.to_csv(prefix.with_name(f"{prefix.name}.recommendation.csv"), index=False)

    print(f"Saved {prefix.with_name(f'{prefix.name}.bucket_summary.csv')}")
    print(bucket_summaries.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
