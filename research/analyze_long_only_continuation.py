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
    parser = argparse.ArgumentParser(description="Analyze richer continuation labels for baseline long trades.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_continuation_round1")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()


def label_trade(frame: pd.DataFrame, trade: pd.Series) -> dict:
    entry_bar = int(trade["EntryBar"])
    entry_row = frame.iloc[entry_bar]
    prev_window = frame.iloc[max(0, entry_bar - 2) : entry_bar + 1].copy()
    future = frame.iloc[entry_bar + 1 : min(entry_bar + 6, len(frame))].copy()

    entry_price = float(trade["EntryPrice"])
    entry_ema20 = float(entry_row["ema20"])
    entry_high = float(entry_row["high"])
    entry_cont_high = float(entry_row["cont_high"]) if pd.notna(entry_row["cont_high"]) else entry_high
    continuation_level = max(entry_high, entry_cont_high)

    recent_touch = bool((prev_window["low"] <= prev_window["ema20"]).any())
    recent_close_below = bool((prev_window["close"] <= prev_window["ema20"]).any())
    reclaimed_ema20 = float(entry_row["close"]) > entry_ema20 and (recent_touch or recent_close_below)

    if future.empty:
        future = frame.iloc[entry_bar : entry_bar + 1].copy()

    closes_above_ema20 = future["close"] >= future["ema20"]
    lows_above_ema20 = future["low"] >= future["ema20"]
    highs_above_level = future["high"] > continuation_level
    closes_above_level = future["close"] > continuation_level
    second_confirmation = bool(
        ((future["close"] > future["open"]) & (future["close"] >= future["ema20"]) & (future["close"] > future["high"].shift(1).fillna(entry_high))).any()
    )
    shallow_retest = bool(((future["low"] <= future["ema20"]) & (future["close"] >= future["ema20"])).any())
    deep_retest = bool((future["close"] < future["ema20"]).any())

    immediate_hold = bool(closes_above_ema20.iloc[:3].all())
    delayed_hold = bool(closes_above_ema20.iloc[:5].tail(min(3, len(closes_above_ema20.iloc[:5]))).all())
    immediate_breakout_hold = bool(highs_above_level.iloc[:3].any() and closes_above_level.iloc[:3].any())
    delayed_breakout_hold = bool(highs_above_level.any() and closes_above_level.any())

    if reclaimed_ema20 and immediate_hold and immediate_breakout_hold:
        continuation_label = "immediate_reclaim_hold"
    elif reclaimed_ema20 and shallow_retest and delayed_hold and delayed_breakout_hold:
        continuation_label = "reclaim_then_delayed_hold"
    elif reclaimed_ema20 and second_confirmation and delayed_breakout_hold and not deep_retest:
        continuation_label = "secondary_confirmation_reclaim"
    elif reclaimed_ema20:
        continuation_label = "reclaim_failed_persistence"
    elif recent_touch:
        continuation_label = "bounce_only_resumption"
    else:
        continuation_label = "ambiguous"

    return {
        "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
        "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
        "Tag": trade["Tag"],
        "PnL": float(trade["PnL"]),
        "ReturnPct": float(trade["ReturnPct"]),
        "continuation_label": continuation_label,
        "reclaimed_ema20": reclaimed_ema20,
        "recent_touch_ema20": recent_touch,
        "recent_close_below_ema20": recent_close_below,
        "immediate_hold_3": immediate_hold,
        "delayed_hold_5": delayed_hold,
        "immediate_breakout_hold_3": immediate_breakout_hold,
        "delayed_breakout_hold_5": delayed_breakout_hold,
        "second_confirmation_5": second_confirmation,
        "shallow_retest_5": shallow_retest,
        "deep_retest_5": deep_retest,
        "entry_exec_distance_atr": float(entry_row["exec_distance_atr"]),
        "entry_atr_ratio": float(entry_row["atr"] / entry_row["atr_ma"]),
        "entry_rsi": float(entry_row["rsi"]),
        "entry_adx": float(entry_row["adx"]),
        "entry_cont_level": continuation_level,
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

    all_dist = distribution(full_labeled, "continuation_label", "all_trades")
    weak_dist = distribution(weak_losers, "continuation_label", "weak_loser")
    winner_dist = distribution(historical_winners, "continuation_label", "historical_winner")

    summary = all_dist.merge(weak_dist, on="continuation_label", how="left").merge(winner_dist, on="continuation_label", how="left")
    summary = summary.fillna(0.0)
    summary["share_gap_vs_winners"] = summary["weak_loser_share"] - summary["historical_winner_share"]
    summary = summary.sort_values(
        ["weak_loser_share", "share_gap_vs_winners", "all_trades_count"],
        ascending=[False, False, False],
    )

    concentrated = summary[
        (summary["weak_loser_count"] >= 2)
        & (summary["weak_loser_share"] >= 0.5)
        & ((summary["weak_loser_share"] - summary["historical_winner_share"]) >= 0.2)
    ]
    recommendation = (
        "enough_subtype_concentration_found"
        if not concentrated.empty
        else "still_no_clean_separation"
    )
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": recommendation,
                "weak_loser_count": len(weak_losers),
                "historical_winner_count": len(historical_winners),
                "top_label": summary.iloc[0]["continuation_label"] if not summary.empty else "none",
                "top_label_weak_loser_share": summary.iloc[0]["weak_loser_share"] if not summary.empty else 0.0,
                "top_label_winner_share": summary.iloc[0]["historical_winner_share"] if not summary.empty else 0.0,
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
