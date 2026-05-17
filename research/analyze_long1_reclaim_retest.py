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
    parser = argparse.ArgumentParser(description="Analyze baseline Long1 reclaim/retest behavior.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long1_reclaim_retest_round1")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()


def select_baseline_long1_trades(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = long_only_production_params()
    bt_config = long_only_backtest_config()
    _, trades = run_backtest(raw_df, params, bt_config)
    frame = build_feature_frame(raw_df, params)
    trades_long1 = trades[trades["Tag"] == "Long1"].copy()
    return frame, trades_long1


def label_long1_trade(frame: pd.DataFrame, trade: pd.Series) -> dict:
    entry_bar = int(trade["EntryBar"])
    exit_bar = int(trade["ExitBar"])
    entry_row = frame.iloc[entry_bar]
    prev_window = frame.iloc[max(0, entry_bar - 2) : entry_bar + 1].copy()
    future = frame.iloc[entry_bar + 1 : min(entry_bar + 6, len(frame))].copy()

    if future.empty:
        future = frame.iloc[entry_bar : entry_bar + 1].copy()

    entry_price = float(trade["EntryPrice"])
    entry_ema20 = float(entry_row["ema20"])
    entry_high = float(entry_row["high"])
    entry_cont_high = float(entry_row["cont_high"]) if pd.notna(entry_row["cont_high"]) else entry_high
    continuation_level = max(entry_high, entry_cont_high)

    recent_touch_ema20 = bool((prev_window["low"] <= prev_window["ema20"]).any())
    recent_close_below_ema20 = bool((prev_window["close"] <= prev_window["ema20"]).any())
    is_reclaim = float(entry_row["close"]) > entry_ema20 and (recent_touch_ema20 or recent_close_below_ema20)

    has_retest = bool(((future["low"] <= future["ema20"]) & (future["close"] >= future["ema20"])).any())
    future_close_below_ema20 = bool((future["close"] < future["ema20"]).any())
    future_breakout_hold = bool(((future["high"] > continuation_level) & (future["close"] > continuation_level)).any())

    holds_reclaim = is_reclaim and (not future_close_below_ema20) and future_breakout_hold
    failed_hold = is_reclaim and (not holds_reclaim)

    if is_reclaim and has_retest and holds_reclaim:
        reclaim_retest_label = "reclaim_retest_hold"
    elif is_reclaim and (not has_retest) and holds_reclaim:
        reclaim_retest_label = "reclaim_no_retest_hold"
    elif failed_hold:
        reclaim_retest_label = "reclaim_failed_hold"
    else:
        reclaim_retest_label = "non_reclaim"

    return {
        "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
        "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
        "Tag": trade["Tag"],
        "PnL": float(trade["PnL"]),
        "ReturnPct": float(trade["ReturnPct"]),
        "reclaim_retest_label": reclaim_retest_label,
        "is_reclaim": is_reclaim,
        "has_retest": has_retest,
        "holds_reclaim": holds_reclaim,
        "failed_hold": failed_hold,
        "recent_touch_ema20": recent_touch_ema20,
        "recent_close_below_ema20": recent_close_below_ema20,
        "future_close_below_ema20": future_close_below_ema20,
        "future_breakout_hold": future_breakout_hold,
        "entry_price": entry_price,
        "entry_ema20": entry_ema20,
        "entry_high": entry_high,
        "entry_cont_high": entry_cont_high,
        "entry_cont_level": continuation_level,
        "entry_exec_distance_atr": float(entry_row["exec_distance_atr"]),
        "entry_atr_ratio": float(entry_row["atr"] / entry_row["atr_ma"]),
        "entry_rsi": float(entry_row["rsi"]),
        "entry_adx": float(entry_row["adx"]),
        "entry_plus_di": float(entry_row["plus_di"]),
        "entry_minus_di": float(entry_row["minus_di"]),
        "held_bars": exit_bar - entry_bar,
    }


def empty_labeled_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "EntryTime",
            "ExitTime",
            "Tag",
            "PnL",
            "ReturnPct",
            "reclaim_retest_label",
            "is_reclaim",
            "has_retest",
            "holds_reclaim",
            "failed_hold",
            "recent_touch_ema20",
            "recent_close_below_ema20",
            "future_close_below_ema20",
            "future_breakout_hold",
            "entry_price",
            "entry_ema20",
            "entry_high",
            "entry_cont_high",
            "entry_cont_level",
            "entry_exec_distance_atr",
            "entry_atr_ratio",
            "entry_rsi",
            "entry_adx",
            "entry_plus_di",
            "entry_minus_di",
            "held_bars",
        ]
    )


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


def build_recommendation(
    summary: pd.DataFrame,
    weak_losers: pd.DataFrame,
    historical_winners: pd.DataFrame,
) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame(
            [
                {
                    "recommendation": "do_not_patch_yet",
                    "weak_loser_count": len(weak_losers),
                    "historical_winner_count": len(historical_winners),
                    "top_label": "none",
                    "top_label_weak_loser_share": 0.0,
                    "top_label_winner_share": 0.0,
                    "top_label_share_gap_vs_winners": 0.0,
                    "qualified_label_count": 0,
                }
            ]
        )

    qualified = summary[
        (summary["reclaim_retest_label"] == "reclaim_failed_hold")
        & (summary["weak_loser_count"] >= 3)
        & (summary["weak_loser_share"] >= 0.50)
        & ((summary["weak_loser_share"] - summary["historical_winner_share"]) >= 0.20)
    ]
    recommendation = "candidate_for_followup_rule_test" if not qualified.empty else "do_not_patch_yet"
    top_row = summary.iloc[0]
    return pd.DataFrame(
        [
            {
                "recommendation": recommendation,
                "weak_loser_count": len(weak_losers),
                "historical_winner_count": len(historical_winners),
                "top_label": top_row["reclaim_retest_label"],
                "top_label_weak_loser_share": top_row["weak_loser_share"],
                "top_label_winner_share": top_row["historical_winner_share"],
                "top_label_share_gap_vs_winners": top_row["share_gap_vs_winners"],
                "qualified_label_count": int(len(qualified)),
            }
        ]
    )


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)

    full_frame, full_trades_long1 = select_baseline_long1_trades(raw_df)
    if full_trades_long1.empty:
        full_labeled = empty_labeled_frame()
    else:
        full_labeled = pd.DataFrame([label_long1_trade(full_frame, trade) for _, trade in full_trades_long1.iterrows()])

    weak_df = slice_frame(raw_df, WEAK_START, WEAK_END)
    weak_frame, weak_trades_long1 = select_baseline_long1_trades(weak_df)
    if weak_trades_long1.empty:
        weak_labeled = empty_labeled_frame()
    else:
        weak_labeled = pd.DataFrame([label_long1_trade(weak_frame, trade) for _, trade in weak_trades_long1.iterrows()])

    weak_losers = weak_labeled[weak_labeled["PnL"] <= 0].copy() if not weak_labeled.empty else weak_labeled.copy()
    historical_winners = full_labeled[full_labeled["PnL"] > 0].copy() if not full_labeled.empty else full_labeled.copy()

    all_dist = distribution(full_labeled, "reclaim_retest_label", "all_trades")
    weak_dist = distribution(weak_losers, "reclaim_retest_label", "weak_loser")
    winner_dist = distribution(historical_winners, "reclaim_retest_label", "historical_winner")

    summary = all_dist.merge(weak_dist, on="reclaim_retest_label", how="left").merge(
        winner_dist, on="reclaim_retest_label", how="left"
    )
    if summary.empty:
        summary = pd.DataFrame(
            columns=[
                "reclaim_retest_label",
                "all_trades_count",
                "all_trades_pnl",
                "all_trades_share",
                "weak_loser_count",
                "weak_loser_pnl",
                "weak_loser_share",
                "historical_winner_count",
                "historical_winner_pnl",
                "historical_winner_share",
                "share_gap_vs_winners",
            ]
        )
    else:
        summary = summary.fillna(0.0)
        summary["share_gap_vs_winners"] = summary["weak_loser_share"] - summary["historical_winner_share"]
        summary = summary.sort_values(
            ["weak_loser_share", "share_gap_vs_winners", "all_trades_count"],
            ascending=[False, False, False],
        )

    recommendation_df = build_recommendation(summary, weak_losers, historical_winners)

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
    if not summary.empty:
        print(summary.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
