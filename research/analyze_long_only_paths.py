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
LOOKBACK_BARS = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze path-dependent setup families for baseline long trades.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_paths_round1")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()


def _count_pushes(series: pd.Series) -> int:
    if len(series) < 3:
        return 0
    count = 0
    vals = series.tolist()
    for i in range(1, len(vals) - 1):
        if vals[i] > vals[i - 1] and vals[i] >= vals[i + 1]:
            count += 1
    return count


def label_path(frame: pd.DataFrame, trade: pd.Series) -> dict:
    entry_bar = int(trade["EntryBar"])
    start_bar = max(0, entry_bar - LOOKBACK_BARS)
    path = frame.iloc[start_bar : entry_bar + 1].copy()
    entry_row = frame.iloc[entry_bar]

    entry_price = float(trade["EntryPrice"])
    entry_atr = float(entry_row["atr"])
    entry_ema20 = float(entry_row["ema20"])
    entry_ema50 = float(entry_row["ema50"])
    cont_high = float(entry_row["cont_high"]) if pd.notna(entry_row["cont_high"]) else float(entry_row["high"])

    pullback_low = float(path["low"].min())
    pullback_depth_atr = max((entry_price - pullback_low) / entry_atr, 0.0)
    closes_above_ema20 = int((path["close"] >= path["ema20"]).sum())
    closes_above_ema50 = int((path["close"] >= path["ema50"]).sum())
    closes_below_ema20 = int((path["close"] < path["ema20"]).sum())
    closes_below_ema50 = int((path["close"] < path["ema50"]).sum())
    ema20_reclaim_bars_ago = next(
        (
            len(path) - 1 - i
            for i in range(len(path) - 1, -1, -1)
            if float(path["close"].iloc[i]) >= float(path["ema20"].iloc[i])
        ),
        len(path),
    )
    volatility_compression = float(path["atr_ratio"].min()) <= 1.0 and float(entry_row["atr_ratio"]) > float(path["atr_ratio"].min())
    di_spread_std = float(path["di_spread"].std(ddof=0)) if len(path) > 1 else 0.0
    close_direction_changes = int((path["close"].diff().fillna(0.0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)).diff().abs() > 1).sum())
    push_count = _count_pushes(path["high"])
    pre_entry_breakout_challenge = bool((path["high"].iloc[:-1] >= cont_high).any()) if len(path) > 1 else False
    close_recovery_atr = (float(path["close"].iloc[-1]) - float(path["close"].iloc[0])) / entry_atr

    if (
        pullback_depth_atr <= 1.25
        and closes_below_ema20 <= 2
        and ema20_reclaim_bars_ago <= 2
        and close_direction_changes <= 2
        and not pre_entry_breakout_challenge
    ):
        label = "clean_pullback_continuation"
    elif (
        volatility_compression
        and ema20_reclaim_bars_ago <= 2
        and close_direction_changes <= 3
        and push_count <= 1
    ):
        label = "compression_release"
    elif (
        closes_below_ema20 >= 3
        and close_direction_changes >= 3
        and di_spread_std >= 4.0
    ):
        label = "noisy_rebound"
    elif (
        ema20_reclaim_bars_ago >= 3
        and closes_above_ema20 >= closes_below_ema20
        and not pre_entry_breakout_challenge
    ):
        label = "late_drift_recovery"
    elif push_count >= 2 or pre_entry_breakout_challenge:
        label = "multi_push_failed_recovery"
    else:
        label = "ambiguous_path"

    return {
        "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
        "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
        "Tag": trade["Tag"],
        "PnL": float(trade["PnL"]),
        "ReturnPct": float(trade["ReturnPct"]),
        "path_label": label,
        "pullback_depth_atr": pullback_depth_atr,
        "closes_above_ema20": closes_above_ema20,
        "closes_above_ema50": closes_above_ema50,
        "closes_below_ema20": closes_below_ema20,
        "closes_below_ema50": closes_below_ema50,
        "ema20_reclaim_bars_ago": ema20_reclaim_bars_ago,
        "volatility_compression": volatility_compression,
        "di_spread_std": di_spread_std,
        "close_direction_changes": close_direction_changes,
        "push_count": push_count,
        "pre_entry_breakout_challenge": pre_entry_breakout_challenge,
        "close_recovery_atr": close_recovery_atr,
        "entry_exec_distance_atr": float(entry_row["exec_distance_atr"]),
        "entry_atr_ratio": float(entry_row["atr_ratio"]),
        "entry_rsi": float(entry_row["rsi"]),
        "entry_adx": float(entry_row["adx"]),
        "entry_price": entry_price,
        "entry_ema20": entry_ema20,
        "entry_ema50": entry_ema50,
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
    full_labeled = pd.DataFrame([label_path(full_frame, trade) for _, trade in full_trades.iterrows()])

    weak_df = slice_frame(raw_df, WEAK_START, WEAK_END)
    _, weak_trades = run_backtest(weak_df, params, bt_config)
    weak_frame = build_feature_frame(weak_df, params)
    weak_labeled = pd.DataFrame([label_path(weak_frame, trade) for _, trade in weak_trades.iterrows()])

    weak_losers = weak_labeled[weak_labeled["PnL"] <= 0].copy()
    historical_winners = full_labeled[full_labeled["PnL"] > 0].copy()

    all_dist = distribution(full_labeled, "path_label", "all_trades")
    weak_dist = distribution(weak_losers, "path_label", "weak_loser")
    winner_dist = distribution(historical_winners, "path_label", "historical_winner")

    summary = all_dist.merge(weak_dist, on="path_label", how="left").merge(winner_dist, on="path_label", how="left")
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
        "strong_enough_path_concentration_found"
        if not concentrated.empty
        else "no_strong_path_concentration"
    )
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": recommendation,
                "weak_loser_count": len(weak_losers),
                "historical_winner_count": len(historical_winners),
                "top_label": summary.iloc[0]["path_label"] if not summary.empty else "none",
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
