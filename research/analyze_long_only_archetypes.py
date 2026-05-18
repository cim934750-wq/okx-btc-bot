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
    parser = argparse.ArgumentParser(description="Analyze trade archetypes for the baseline long-only strategy.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_archetypes_round1")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index <= end)].copy()


def label_archetype(row: pd.Series) -> str:
    if row["entry_extension_atr"] >= 1.8 or row["ema20_gap_atr"] >= 1.0:
        return "late_expansion_chase"
    if (
        row["atr_ratio"] < 1.0
        and row["di_spread"] < 10.0
        and (row["close_change_2_atr"] <= 0.0 or row["closes_above_entry_3"] <= 1)
    ):
        return "noisy_transition"
    if (
        row["early_upside_3_atr"] >= 1.25
        and row["close_change_2_atr"] >= 0.5
        and row["closes_above_entry_3"] >= 2
        and row["atr_ratio"] >= 1.0
    ):
        return "clean_continuation"
    if (
        row["early_upside_3_atr"] >= 0.75
        and row["close_change_2_atr"] >= 0.0
        and row["closes_above_entry_3"] >= 2
    ):
        return "steady_continuation"
    return "fragile_breakout"


def build_trade_features(frame: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, trade in trades.iterrows():
        entry_bar = int(trade["EntryBar"])
        entry_row = frame.iloc[entry_bar]
        entry_price = float(trade["EntryPrice"])
        entry_atr = float(entry_row["atr"])
        future = frame.iloc[entry_bar + 1 : min(entry_bar + 4, len(frame))].copy()
        if future.empty:
            future = frame.iloc[entry_bar : entry_bar + 1].copy()

        max_high = float(future["high"].max())
        min_low = float(future["low"].min())
        close_2 = float(future["close"].iloc[min(1, len(future) - 1)])

        row = {
            "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
            "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
            "Tag": trade["Tag"],
            "PnL": float(trade["PnL"]),
            "ReturnPct": float(trade["ReturnPct"]),
            "entry_extension_atr": float(entry_row["exec_distance_atr"]),
            "pullback_band_position_atr": float((entry_row["close"] - entry_row["ema50"]) / entry_atr),
            "ema20_gap_atr": float(entry_row.get("close_ema20_gap_atr", 0.0)),
            "atr_ratio": float(entry_row.get("atr_ratio", entry_row["atr"] / entry_row["atr_ma"])),
            "adx": float(entry_row["adx"]),
            "rsi": float(entry_row["rsi"]),
            "di_spread": float(entry_row.get("di_spread", entry_row["plus_di"] - entry_row["minus_di"])),
            "early_upside_3_atr": (max_high - entry_price) / entry_atr,
            "early_drawdown_3_atr": (entry_price - min_low) / entry_atr,
            "close_change_2_atr": (close_2 - entry_price) / entry_atr,
            "closes_above_entry_3": int((future["close"] > entry_price).sum()),
            "closes_above_ema20_3": int((future["close"] > future["ema20"]).sum()),
            "weekly_bull": bool(entry_row["weekly_bull"]),
            "daily_bull": bool(entry_row["daily_bull"]),
        }
        row["archetype_label"] = label_archetype(pd.Series(row))
        rows.append(row)
    return pd.DataFrame(rows)


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


def recommendation_from_summary(summary: pd.DataFrame) -> str:
    if summary.empty:
        return "no_strong_archetype_concentration"
    strong = summary[
        (summary["weak_loser_count"] >= 2)
        & (summary["weak_loser_share"] >= 0.5)
        & ((summary["weak_loser_share"] - summary["historical_winner_share"]) >= 0.2)
    ]
    return "one_archetype_based_follow_up_is_justified" if not strong.empty else "no_strong_archetype_concentration"


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    params = long_only_production_params()
    bt_config = long_only_backtest_config()

    full_stats, full_trades = run_backtest(raw_df, params, bt_config)
    full_frame = build_feature_frame(raw_df, params)
    full_features = build_trade_features(full_frame, full_trades)

    weak_df = slice_frame(raw_df, WEAK_START, WEAK_END)
    weak_stats, weak_trades = run_backtest(weak_df, params, bt_config)
    weak_frame = build_feature_frame(weak_df, params)
    weak_features = build_trade_features(weak_frame, weak_trades)
    weak_losers = weak_features[weak_features["PnL"] <= 0].copy()
    historical_winners = full_features[full_features["PnL"] > 0].copy()

    all_dist = distribution(full_features, "archetype_label", "all_trades")
    weak_dist = distribution(weak_losers, "archetype_label", "weak_loser")
    winner_dist = distribution(historical_winners, "archetype_label", "historical_winner")
    summary = (
        all_dist.merge(weak_dist, on="archetype_label", how="left")
        .merge(winner_dist, on="archetype_label", how="left")
        .fillna(0.0)
    )
    summary["share_gap_vs_winners"] = summary["weak_loser_share"] - summary["historical_winner_share"]
    summary = summary.sort_values(
        ["weak_loser_share", "share_gap_vs_winners", "all_trades_count"],
        ascending=[False, False, False],
    )

    recommendation = recommendation_from_summary(summary)
    recommendation_df = pd.DataFrame(
        [
            {
                "recommendation": recommendation,
                "weak_loser_count": len(weak_losers),
                "historical_winner_count": len(historical_winners),
                "top_archetype": summary.iloc[0]["archetype_label"] if not summary.empty else "none",
                "top_archetype_weak_loser_share": summary.iloc[0]["weak_loser_share"] if not summary.empty else 0.0,
                "top_archetype_winner_share": summary.iloc[0]["historical_winner_share"] if not summary.empty else 0.0,
            }
        ]
    )

    prefix = paths.output_dir / args.prefix
    full_features.to_csv(prefix.with_name(f"{prefix.name}.trade_features_all.csv"), index=False)
    weak_features.to_csv(prefix.with_name(f"{prefix.name}.trade_features_2025_2026.csv"), index=False)
    all_dist.to_csv(prefix.with_name(f"{prefix.name}.archetype_distribution_all_trades.csv"), index=False)
    weak_dist.to_csv(prefix.with_name(f"{prefix.name}.archetype_distribution_2025_2026_losers.csv"), index=False)
    winner_dist.to_csv(prefix.with_name(f"{prefix.name}.archetype_distribution_historical_winners.csv"), index=False)
    summary.to_csv(prefix.with_name(f"{prefix.name}.archetype_concentration_summary.csv"), index=False)
    recommendation_df.to_csv(prefix.with_name(f"{prefix.name}.recommendation.csv"), index=False)

    print(f"Saved {prefix.with_name(f'{prefix.name}.trade_features_all.csv')}")
    print(f"Saved {prefix.with_name(f'{prefix.name}.archetype_concentration_summary.csv')}")
    print(summary.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
