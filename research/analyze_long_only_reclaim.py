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
    parser = argparse.ArgumentParser(description="Analyze reclaim/retest/hold labels for baseline long trades.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_reclaim_round1")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()


def label_trade(frame: pd.DataFrame, trade: pd.Series) -> dict:
    entry_bar = int(trade["EntryBar"])
    entry_row = frame.iloc[entry_bar]
    prev_window = frame.iloc[max(0, entry_bar - 2) : entry_bar + 1].copy()
    future = frame.iloc[entry_bar + 1 : min(entry_bar + 4, len(frame))].copy()

    entry_price = float(trade["EntryPrice"])
    entry_ema20 = float(entry_row["ema20"])
    entry_cont_high = float(entry_row["cont_high"]) if pd.notna(entry_row["cont_high"]) else float(entry_row["high"])

    recent_touch = bool((prev_window["low"] <= prev_window["ema20"]).any())
    recent_close_below = bool((prev_window["close"] <= prev_window["ema20"]).any())
    reclaimed_ema20 = float(entry_row["close"]) > entry_ema20 and (recent_touch or recent_close_below)

    if future.empty:
        hold_above_ema20 = False
        continuation_confirmed = False
        retest_seen = False
        shallow_retest = False
        deep_retest = False
        closes_above_ema20 = 0
    else:
        hold_above_ema20 = bool((future["close"] >= future["ema20"]).all())
        continuation_confirmed = bool((future["high"] > max(float(entry_row["high"]), entry_cont_high)).any())
        retest_seen = bool((future["low"] <= future["ema20"]).any())
        shallow_retest = bool(((future["low"] <= future["ema20"]) & (future["close"] >= future["ema20"])).any())
        deep_retest = bool((future["close"] < future["ema20"]).any())
        closes_above_ema20 = int((future["close"] >= future["ema20"]).sum())

    if reclaimed_ema20 and shallow_retest and hold_above_ema20 and continuation_confirmed and not deep_retest:
        reclaim_label = "strict_reclaim_retest_hold"
    elif reclaimed_ema20 and shallow_retest and (deep_retest or not hold_above_ema20):
        reclaim_label = "reclaim_then_failed_hold"
    elif reclaimed_ema20 and (not retest_seen) and continuation_confirmed:
        reclaim_label = "reclaim_without_retest"
    elif recent_touch and not reclaimed_ema20:
        reclaim_label = "bounce_only_resumption"
    else:
        reclaim_label = "ambiguous"

    return {
        "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
        "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
        "Tag": trade["Tag"],
        "PnL": float(trade["PnL"]),
        "ReturnPct": float(trade["ReturnPct"]),
        "reclaim_label": reclaim_label,
        "reclaimed_ema20": reclaimed_ema20,
        "recent_touch_ema20": recent_touch,
        "recent_close_below_ema20": recent_close_below,
        "hold_above_ema20_3": hold_above_ema20,
        "retest_seen_3": retest_seen,
        "shallow_retest_3": shallow_retest,
        "deep_retest_3": deep_retest,
        "continuation_confirmed_3": continuation_confirmed,
        "closes_above_ema20_3": closes_above_ema20,
        "entry_close": float(entry_row["close"]),
        "entry_ema20": entry_ema20,
        "entry_high": float(entry_row["high"]),
        "entry_cont_high": entry_cont_high,
        "entry_exec_distance_atr": float(entry_row["exec_distance_atr"]),
        "entry_atr_ratio": float(entry_row["atr"] / entry_row["atr_ma"]),
        "entry_rsi": float(entry_row["rsi"]),
        "entry_adx": float(entry_row["adx"]),
        "entry_price": entry_price,
    }


def distribution(df: pd.DataFrame, label_col: str, prefix: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[label_col, f"{prefix}_count", f"{prefix}_pnl", f"{prefix}_share"])
    out = (
        df.groupby(label_col, dropna=False)
        .agg(**{f"{prefix}_count": ("PnL", "size"), f"{prefix}_pnl": ("PnL", "sum")})
        .reset_index()
    )
    out[f"{prefix}_share"] = out[f"{prefix}_count"] / max(float(len(df)), 1.0)
    return out


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    params = long_only_production_params()
    bt_config = long_only_backtest_config()

    _, full_trades = run_backtest(raw_df, params, bt_config)
    full_frame = build_feature_frame(raw_df, params)
    full_labeled = pd.DataFrame([label_trade(full_frame, trade) for _, trade in full_trades.iterrows()])

    weak_df = slice_frame(raw_df, WEAK_START, WEAK_END)
    _, weak_trades = run_backtest(weak_df, params, bt_config)
    weak_frame = build_feature_frame(weak_df, params)
    weak_labeled = pd.DataFrame([label_trade(weak_frame, trade) for _, trade in weak_trades.iterrows()])

    weak_losers = weak_labeled[weak_labeled["PnL"] <= 0].copy()
    historical_winners = full_labeled[full_labeled["PnL"] > 0].copy()

    all_dist = distribution(full_labeled, "reclaim_label", "all_trades")
    weak_dist = distribution(weak_losers, "reclaim_label", "weak_loser")
    winner_dist = distribution(historical_winners, "reclaim_label", "historical_winner")

    summary = all_dist.merge(weak_dist, on="reclaim_label", how="left").merge(winner_dist, on="reclaim_label", how="left")
    summary = summary.fillna(0.0)
    summary["share_gap_vs_winners"] = summary["weak_loser_share"] - summary["historical_winner_share"]
    summary = summary.sort_values(
        ["weak_loser_share", "share_gap_vs_winners", "all_trades_count"],
        ascending=[False, False, False],
    )

    non_strict_weak_share = float(
        weak_losers[weak_losers["reclaim_label"] != "strict_reclaim_retest_hold"].shape[0] / max(len(weak_losers), 1)
    )
    non_strict_winner_share = float(
        historical_winners[historical_winners["reclaim_label"] != "strict_reclaim_retest_hold"].shape[0] / max(len(historical_winners), 1)
    )
    justified = (non_strict_weak_share >= 0.67) and ((non_strict_weak_share - non_strict_winner_share) >= 0.2)
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": "strong_enough_separation_found" if justified else "no_strong_reclaim_retest_separation",
                "weak_loser_count": len(weak_losers),
                "historical_winner_count": len(historical_winners),
                "non_strict_weak_share": non_strict_weak_share,
                "non_strict_winner_share": non_strict_winner_share,
            }
        ]
    )

    prefix = paths.output_dir / args.prefix
    full_labeled.to_csv(prefix.with_name(f"{prefix.name}.trade_labels_all.csv"), index=False)
    weak_labeled.to_csv(prefix.with_name(f"{prefix.name}.trade_labels_2025_2026.csv"), index=False)
    all_dist.to_csv(prefix.with_name(f"{prefix.name}.label_distribution_all_trades.csv"), index=False)
    weak_dist.to_csv(prefix.with_name(f"{prefix.name}.label_distribution_2025_2026_losers.csv"), index=False)
    winner_dist.to_csv(prefix.with_name(f"{prefix.name}.label_distribution_historical_winners.csv"), index=False)
    summary.to_csv(prefix.with_name(f"{prefix.name}.label_concentration_summary.csv"), index=False)
    recommendation_df.to_csv(prefix.with_name(f"{prefix.name}.recommendation.csv"), index=False)

    print(f"Saved {prefix.with_name(f'{prefix.name}.trade_labels_all.csv')}")
    print(f"Saved {prefix.with_name(f'{prefix.name}.label_concentration_summary.csv')}")
    print(summary.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
