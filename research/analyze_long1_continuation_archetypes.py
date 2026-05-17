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
    parser = argparse.ArgumentParser(description="Decompose baseline Long1 trades into continuation archetypes.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long1_continuation_archetypes_round1")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()


def label_trade(frame: pd.DataFrame, trade: pd.Series) -> dict:
    entry_bar = int(trade["EntryBar"])
    entry_row = frame.iloc[entry_bar]
    prev_window = frame.iloc[max(0, entry_bar - 2) : entry_bar + 1].copy()

    entry_close = float(entry_row["close"])
    entry_ema20 = float(entry_row["ema20"])
    entry_cont_high = float(entry_row["cont_high"]) if pd.notna(entry_row["cont_high"]) else float(entry_row["high"])
    entry_atr = float(entry_row["atr"])
    entry_cont_gap_atr = max(entry_cont_high - entry_close, 0.0) / entry_atr if entry_atr > 0 else 0.0
    recent_touch_ema20 = bool((prev_window["low"] <= prev_window["ema20"]).any())
    recent_close_below_ema20 = bool((prev_window["close"] <= prev_window["ema20"]).any())
    has_reclaim_evidence = entry_close > entry_ema20 and recent_close_below_ema20
    breakout_relation = ((entry_close >= entry_cont_high) or (entry_cont_gap_atr <= 0.10)) and (not recent_close_below_ema20)
    momentum_gap_atr = float(entry_row.get("close_ema20_gap_atr", 0.0))

    if str(entry_row["regime_label"]) == "weakening_trend":
        archetype = "late_stage_weakening_continuation"
    elif breakout_relation:
        archetype = "breakout_continuation"
    elif has_reclaim_evidence:
        archetype = "reclaim_continuation"
    else:
        archetype = "shallow_pullback_momentum_continuation"

    return {
        "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
        "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
        "Tag": trade["Tag"],
        "PnL": float(trade["PnL"]),
        "ReturnPct": float(trade["ReturnPct"]),
        "continuation_archetype": archetype,
        "regime_label": str(entry_row["regime_label"]),
        "recent_touch_ema20": recent_touch_ema20,
        "recent_close_below_ema20": recent_close_below_ema20,
        "has_reclaim_evidence": has_reclaim_evidence,
        "entry_close": entry_close,
        "entry_ema20": entry_ema20,
        "entry_cont_high": entry_cont_high,
        "entry_cont_gap_atr": entry_cont_gap_atr,
        "entry_exec_distance_atr": float(entry_row["exec_distance_atr"]),
        "entry_atr_ratio": float(entry_row["atr_ratio"]),
        "entry_adx": float(entry_row["adx"]),
        "entry_di_spread": float(entry_row["di_spread"]),
        "entry_rsi": float(entry_row["rsi"]),
        "entry_close_ema20_gap_atr": momentum_gap_atr,
    }


def label_baseline_long1(raw_df: pd.DataFrame) -> pd.DataFrame:
    params = long_only_production_params()
    bt_config = long_only_backtest_config()
    _, trades = run_backtest(raw_df, params, bt_config)
    long1_trades = trades[trades["Tag"] == "Long1"].copy()
    frame = build_feature_frame(raw_df, params)
    if long1_trades.empty:
        return pd.DataFrame(
            columns=[
                "EntryTime",
                "ExitTime",
                "Tag",
                "PnL",
                "ReturnPct",
                "continuation_archetype",
                "regime_label",
                "recent_touch_ema20",
                "recent_close_below_ema20",
                "has_reclaim_evidence",
                "entry_close",
                "entry_ema20",
                "entry_cont_high",
                "entry_cont_gap_atr",
                "entry_exec_distance_atr",
                "entry_atr_ratio",
                "entry_adx",
                "entry_di_spread",
                "entry_rsi",
                "entry_close_ema20_gap_atr",
            ]
        )
    return pd.DataFrame([label_trade(frame, trade) for _, trade in long1_trades.iterrows()])


def distribution(df: pd.DataFrame, label_col: str, prefix: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[label_col, f"{prefix}_count", f"{prefix}_losers", f"{prefix}_winners", f"{prefix}_loser_share", f"{prefix}_avg_pnl"]
        )
    grouped = df.groupby(label_col, dropna=False)
    out = grouped["PnL"].agg(["count", "mean"]).reset_index()
    out = out.rename(columns={"count": f"{prefix}_count", "mean": f"{prefix}_avg_pnl"})
    loser_counts = grouped["PnL"].apply(lambda s: int((s <= 0).sum())).reset_index(name=f"{prefix}_losers")
    winner_counts = grouped["PnL"].apply(lambda s: int((s > 0).sum())).reset_index(name=f"{prefix}_winners")
    out = out.merge(loser_counts, on=label_col, how="left").merge(winner_counts, on=label_col, how="left")
    out[f"{prefix}_loser_share"] = out[f"{prefix}_losers"] / out[f"{prefix}_count"].clip(lower=1)
    return out


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)

    full_labeled = label_baseline_long1(raw_df)
    weak_df = slice_frame(raw_df, WEAK_START, WEAK_END)
    weak_labeled = label_baseline_long1(weak_df)
    all_losers = full_labeled[full_labeled["PnL"] <= 0].copy()
    historical_winners = full_labeled[full_labeled["PnL"] > 0].copy()

    all_dist = distribution(full_labeled, "continuation_archetype", "all_trades")
    loser_dist = distribution(all_losers, "continuation_archetype", "all_losers")
    winner_dist = distribution(historical_winners, "continuation_archetype", "historical_winners")

    summary = (
        all_dist.merge(loser_dist, on="continuation_archetype", how="left")
        .merge(winner_dist, on="continuation_archetype", how="left")
        .fillna(0.0)
    )
    summary["loser_share_gap_vs_winners"] = summary["all_losers_loser_share"] - summary["historical_winners_loser_share"]
    summary["loser_concentration_gap"] = (
        (summary["all_losers_count"] / max(float(len(all_losers)), 1.0))
        - (summary["historical_winners_count"] / max(float(len(historical_winners)), 1.0))
    )
    summary = summary.sort_values(
        ["loser_concentration_gap", "all_trades_loser_share", "all_trades_count"],
        ascending=[False, False, False],
    )

    blended = (
        len(summary) >= 2
        and (summary["all_trades_count"] > 0).sum() >= 2
        and (
            (
                summary["all_losers_count"] / max(float(len(all_losers)), 1.0)
                - summary["historical_winners_count"] / max(float(len(historical_winners)), 1.0)
            ).abs().max()
            >= 0.15
        )
    )
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": "blended_continuation_basket_supported" if blended else "single_setup_still_plausible",
                "all_long1_count": len(full_labeled),
                "all_loser_count": len(all_losers),
                "historical_winner_count": len(historical_winners),
                "top_loser_archetype": summary.iloc[0]["continuation_archetype"] if not summary.empty else "none",
                "top_loser_concentration_gap": summary.iloc[0]["loser_concentration_gap"] if not summary.empty else 0.0,
                "top_loser_share": summary.iloc[0]["all_trades_loser_share"] if not summary.empty else 0.0,
            }
        ]
    )

    prefix = paths.output_dir / args.prefix
    full_labeled.to_csv(prefix.with_name(f"{prefix.name}.trade_labels_all.csv"), index=False)
    weak_labeled.to_csv(prefix.with_name(f"{prefix.name}.trade_labels_2025_2026.csv"), index=False)
    all_dist.to_csv(prefix.with_name(f"{prefix.name}.archetype_distribution_all_trades.csv"), index=False)
    winner_dist.to_csv(prefix.with_name(f"{prefix.name}.archetype_distribution_historical_winners.csv"), index=False)
    loser_dist.to_csv(prefix.with_name(f"{prefix.name}.archetype_distribution_all_losers.csv"), index=False)
    summary.to_csv(prefix.with_name(f"{prefix.name}.archetype_concentration_summary.csv"), index=False)
    recommendation_df.to_csv(prefix.with_name(f"{prefix.name}.recommendation.csv"), index=False)

    print(f"Saved {prefix.with_name(f'{prefix.name}.trade_labels_all.csv')}")
    print(f"Saved {prefix.with_name(f'{prefix.name}.archetype_concentration_summary.csv')}")
    print(summary.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
