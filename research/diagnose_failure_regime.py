from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from research.config import BacktestConfig, Paths, StrategyParams
from research.data import load_ohlcv_csv
from research.indicators import build_feature_frame
from research.strategy import extract_metrics, run_backtest


SEGMENT_START = "2025-01-01"
SEGMENT_END = "2026-04-12 23:59:59"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose failure regime for BTC MTF strategy.")
    parser.add_argument("--csv", required=True, help="Path to 4H OHLCV CSV.")
    parser.add_argument("--prefix", default="failure_2025_2026", help="Output file prefix.")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    return df[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index <= pd.Timestamp(end, tz="UTC"))].copy()


def state_from_flags(bull: bool, bear: bool) -> str:
    if bull:
        return "bull"
    if bear:
        return "bear"
    return "neutral"


def trade_type_from_tag(tag: str) -> str:
    if tag in {"Long1", "Short1"}:
        return "pullback_entry"
    if tag in {"Long2", "Short2"}:
        return "add_on_entry"
    return "unknown"


def summarize_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = df.groupby(group_col, dropna=False)
    out = grouped["PnL"].agg(["count", "sum", "mean", "median"])
    out = out.rename(columns={"count": "trades", "sum": "net_pnl", "mean": "avg_trade", "median": "median_trade"})
    out["win_rate"] = grouped["PnL"].apply(lambda s: float((s > 0).mean() * 100.0))
    out["gross_profit"] = grouped["PnL"].apply(lambda s: float(s[s > 0].sum()))
    out["gross_loss"] = grouped["PnL"].apply(lambda s: float(-s[s < 0].sum()))
    out["profit_factor"] = np.where(out["gross_loss"] > 0, out["gross_profit"] / out["gross_loss"], np.inf)
    return out.reset_index().sort_values("net_pnl")


def enrich_trades(frame: pd.DataFrame, trades: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    if trades.empty:
        return trades

    data = trades.copy()
    data["EntryTime"] = pd.to_datetime(data["EntryTime"], utc=True)
    data["ExitTime"] = pd.to_datetime(data["ExitTime"], utc=True)
    data["entry_ts"] = pd.to_datetime(frame.index.to_series().iloc[data["EntryBar"].astype(int)].values, utc=True)
    data["exit_ts"] = pd.to_datetime(frame.index.to_series().iloc[data["ExitBar"].astype(int)].values, utc=True)
    data["direction"] = np.where(data["Size"] > 0, "long", "short")
    data["trade_type"] = data["Tag"].map(trade_type_from_tag)
    data["entry_month"] = data["EntryTime"].dt.to_period("M").astype(str)

    entry_features = frame.copy()
    entry_features["weekly_bias_state"] = [
        state_from_flags(bull, bear) for bull, bear in zip(entry_features["weekly_bull"], entry_features["weekly_bear"])
    ]
    entry_features["daily_state"] = [
        state_from_flags(bull, bear) for bull, bear in zip(entry_features["daily_bull"], entry_features["daily_bear"])
    ]
    entry_features["atr_ratio"] = entry_features["atr"] / entry_features["atr_ma"]
    entry_features = entry_features[
        [
            "weekly_bias_state",
            "daily_state",
            "adx",
            "atr",
            "atr_ratio",
            "rsi",
            "ema20",
            "ema50",
            "ema200",
            "exec_distance_atr",
            "short_distance_cap_pass",
            "short_ema20_gap_atr",
            "short_ema20_proximity_pass",
            "short_squeeze_risk",
            "short_squeeze_pass",
            "long_pullback",
            "short_pullback",
            "exec_bull_structure",
            "exec_bear_structure",
            "exec_bull_momentum",
            "exec_bear_momentum",
            "starter_long_signal",
            "starter_short_signal",
            "add_long_signal",
            "add_short_signal",
        ]
    ].copy()
    entry_features["entry_ts"] = pd.to_datetime(entry_features.index, utc=True)

    data = data.merge(entry_features, on="entry_ts", how="left")
    data["loss_flag"] = data["PnL"] <= 0
    data["tp_hit_flag"] = data["ReturnPct"] > 0
    data["adverse_move"] = np.where(
        data["direction"] == "long",
        (data["EntryPrice"] - data["ExitPrice"]).clip(lower=0.0),
        (data["ExitPrice"] - data["EntryPrice"]).clip(lower=0.0),
    )
    data["adverse_atr_multiple"] = data["adverse_move"] / data["atr"].replace(0.0, np.nan)
    data["stop_overshoot_flag"] = data["adverse_atr_multiple"] > params.stop_atr_mult * 1.1
    data["held_bars"] = data["ExitBar"] - data["EntryBar"]
    data["distance_bucket"] = pd.cut(
        data["exec_distance_atr"],
        bins=[-np.inf, 0.05, 0.10, 0.20, np.inf],
        labels=["<=0.05", "0.05-0.10", "0.10-0.20", ">0.20"],
    )
    data["adx_bucket"] = pd.cut(
        data["adx"],
        bins=[-np.inf, 16, 20, 25, np.inf],
        labels=["<=16", "16-20", "20-25", ">25"],
    )
    data["atr_ratio_bucket"] = pd.cut(
        data["atr_ratio"],
        bins=[-np.inf, 0.90, 1.00, 1.10, np.inf],
        labels=["<=0.90", "0.90-1.00", "1.00-1.10", ">1.10"],
    )
    return data


def plot_monthly(monthly: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#2e8b57" if x >= 0 else "#b22222" for x in monthly["net_pnl"]]
    ax.bar(monthly["entry_month"], monthly["net_pnl"], color=colors)
    ax.set_title("2025-2026 Monthly Net PnL")
    ax.set_ylabel("PnL")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_cumulative(trades: pd.DataFrame, out_path: Path) -> None:
    ordered = trades.sort_values("ExitTime").copy()
    ordered["cum_pnl"] = ordered["PnL"].cumsum()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(ordered["ExitTime"], ordered["cum_pnl"], color="#1f77b4", linewidth=2)
    ax.set_title("2025-2026 Cumulative Trade PnL")
    ax.set_ylabel("Cumulative PnL")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_category(summary: pd.DataFrame, category_col: str, out_path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ["#2e8b57" if x >= 0 else "#b22222" for x in summary["net_pnl"]]
    ax.bar(summary[category_col].astype(str), summary["net_pnl"], color=colors)
    ax.set_title(title)
    ax.set_ylabel("Net PnL")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    segment_df = slice_frame(raw_df, SEGMENT_START, SEGMENT_END)
    params = StrategyParams()
    bt_config = BacktestConfig()

    stats, trades = run_backtest(segment_df, params, bt_config)
    metrics = extract_metrics(stats, trades)
    feature_frame = build_feature_frame(segment_df, params)
    enriched = enrich_trades(feature_frame, trades, params)

    prefix = paths.output_dir / args.prefix

    metrics_df = pd.DataFrame([metrics])
    direction_summary = summarize_group(enriched, "direction")
    month_summary = summarize_group(enriched, "entry_month")
    trade_type_summary = summarize_group(enriched, "trade_type")
    weekly_bias_summary = summarize_group(enriched, "weekly_bias_state")
    daily_state_summary = summarize_group(enriched, "daily_state")
    distance_summary = summarize_group(enriched, "distance_bucket")
    adx_summary = summarize_group(enriched, "adx_bucket")
    atr_ratio_summary = summarize_group(enriched, "atr_ratio_bucket")
    tag_summary = summarize_group(enriched, "Tag")
    stop_overshoot_summary = summarize_group(enriched, "stop_overshoot_flag")

    enriched.to_csv(prefix.with_name(prefix.name + "_trades_enriched.csv"), index=False)
    metrics_df.to_csv(prefix.with_name(prefix.name + "_metrics.csv"), index=False)
    direction_summary.to_csv(prefix.with_name(prefix.name + "_direction_summary.csv"), index=False)
    month_summary.to_csv(prefix.with_name(prefix.name + "_month_summary.csv"), index=False)
    trade_type_summary.to_csv(prefix.with_name(prefix.name + "_trade_type_summary.csv"), index=False)
    weekly_bias_summary.to_csv(prefix.with_name(prefix.name + "_weekly_bias_summary.csv"), index=False)
    daily_state_summary.to_csv(prefix.with_name(prefix.name + "_daily_state_summary.csv"), index=False)
    distance_summary.to_csv(prefix.with_name(prefix.name + "_distance_summary.csv"), index=False)
    adx_summary.to_csv(prefix.with_name(prefix.name + "_adx_summary.csv"), index=False)
    atr_ratio_summary.to_csv(prefix.with_name(prefix.name + "_atr_ratio_summary.csv"), index=False)
    tag_summary.to_csv(prefix.with_name(prefix.name + "_tag_summary.csv"), index=False)
    stop_overshoot_summary.to_csv(prefix.with_name(prefix.name + "_stop_overshoot_summary.csv"), index=False)

    if not month_summary.empty:
        plot_monthly(month_summary.sort_values("entry_month"), prefix.with_name(prefix.name + "_monthly_pnl.png"))
    if not enriched.empty:
        plot_cumulative(enriched, prefix.with_name(prefix.name + "_cumulative_pnl.png"))
    if not direction_summary.empty:
        plot_category(direction_summary, "direction", prefix.with_name(prefix.name + "_direction_pnl.png"), "PnL by Direction")
    if not trade_type_summary.empty:
        plot_category(trade_type_summary, "trade_type", prefix.with_name(prefix.name + "_trade_type_pnl.png"), "PnL by Trade Type")

    print("Segment metrics")
    print(metrics_df.to_string(index=False))
    print("\nDirection summary")
    print(direction_summary.to_string(index=False))
    print("\nTrade type summary")
    print(trade_type_summary.to_string(index=False))
    print("\nWeekly bias summary")
    print(weekly_bias_summary.to_string(index=False))
    print("\nDaily state summary")
    print(daily_state_summary.to_string(index=False))
    print("\nMonth summary")
    print(month_summary.to_string(index=False))
    print("\nStop overshoot summary")
    print(stop_overshoot_summary.to_string(index=False))


if __name__ == "__main__":
    main()
