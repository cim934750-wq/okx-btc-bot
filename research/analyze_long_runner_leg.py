from __future__ import annotations

import argparse

import pandas as pd

from research.config import Paths
from research.data import load_ohlcv_csv
from research.indicators import build_feature_frame
from research.long_only_candidate import long_only_backtest_config, long_only_production_params_with_fix
from research.strategy import run_backtest


SEGMENT_START = pd.Timestamp("2025-01-01", tz="UTC")
SEGMENT_END = pd.Timestamp("2026-04-12 23:59:59", tz="UTC")
FRACTIONAL_UNIT = 1 / 100e6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze long-only runner leg behavior after broker TP1 patch.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_candidate_after_tp1broker")
    return parser.parse_args()


def in_segment(ts: pd.Timestamp) -> bool:
    return SEGMENT_START <= ts <= SEGMENT_END


def slice_segment(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df.index >= SEGMENT_START) & (df.index <= SEGMENT_END)].copy()


def build_runner_stop_path(
    frame: pd.DataFrame,
    entry_bar: int,
    exit_bar: int,
    entry_price: float,
    params,
    commission_rate: float,
) -> tuple[pd.DataFrame, bool, bool]:
    sub = frame.iloc[entry_bar : exit_bar + 1].copy()
    highest = float(sub["high"].iloc[0])
    tp1_hit = False
    tp2_hit = False
    rows: list[dict] = []

    for offset, (timestamp, row) in enumerate(sub.iterrows()):
        atr = float(row["atr"])
        risk = atr * params.stop_atr_mult
        base_stop = entry_price - risk
        tp1 = entry_price + risk * params.tp1_rr
        tp2 = entry_price + risk * params.tp2_rr
        highest = max(highest, float(row["high"]))
        if float(row["high"]) >= tp1:
            tp1_hit = True
        if float(row["high"]) >= tp2:
            tp2_hit = True

        fee_buffer = entry_price * commission_rate * 2.0
        break_even = entry_price + fee_buffer + atr * params.breakeven_offset_atr if tp1_hit else base_stop
        active_trail_mult = params.trail_atr_mult
        trail_raw = highest - atr * active_trail_mult
        runner_stop = max(break_even, trail_raw)

        rows.append(
            {
                "timestamp": timestamp,
                "bar_offset": offset,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "atr": atr,
                "ema20": float(row["ema20"]),
                "ema50": float(row["ema50"]),
                "highest_since_entry": highest,
                "base_stop": base_stop,
                "tp1_price_theoretical": tp1,
                "tp2_price_theoretical": tp2,
                "tp1_hit_theoretical": tp1_hit,
                "tp2_hit_theoretical": tp2_hit,
                "break_even_floor": break_even,
                "trail_raw": trail_raw,
                "runner_stop_theoretical": runner_stop,
            }
        )

    return pd.DataFrame(rows), tp1_hit, tp2_hit


def main() -> None:
    args = parse_args()
    paths = Paths()
    params = long_only_production_params_with_fix()
    bt_config = long_only_backtest_config()
    raw_df = load_ohlcv_csv(args.csv)
    segment_df = slice_segment(raw_df)
    frame = build_feature_frame(segment_df, params)
    _, trades = run_backtest(segment_df, params, bt_config)

    trades = trades.copy()
    trades["EntryTime"] = pd.to_datetime(trades["EntryTime"], utc=True)
    trades["ExitTime"] = pd.to_datetime(trades["ExitTime"], utc=True)
    trades = trades[
        trades["Tag"].isin(["Long1_TP1", "Long1_Run"])
    ].sort_values(["EntryTime", "Tag"])

    lifecycle_rows: list[dict] = []
    stop_path_frames: list[pd.DataFrame] = []

    for entry_time, group in trades.groupby("EntryTime", sort=True):
        group = group.sort_values("Tag")
        runner_leg = group[group["Tag"] == "Long1_Run"].iloc[0]
        tp1_leg = group[group["Tag"] == "Long1_TP1"].iloc[0]

        entry_price = float(runner_leg["EntryPrice"])
        entry_bar = int(runner_leg["EntryBar"])
        exit_bar = int(runner_leg["ExitBar"])
        stop_path, tp1_theoretical, tp2_theoretical = build_runner_stop_path(
            frame=frame,
            entry_bar=entry_bar,
            exit_bar=exit_bar,
            entry_price=entry_price,
            params=params,
            commission_rate=bt_config.commission,
        )
        stop_path["lifecycle_entry_time"] = entry_time
        stop_path_frames.append(stop_path)

        scaled_entry_ref = entry_price * FRACTIONAL_UNIT
        risk_unscaled = float(frame.iloc[entry_bar]["atr"]) * params.stop_atr_mult
        risk_scaled = risk_unscaled * FRACTIONAL_UNIT
        broker_tp_from_fixed_code = scaled_entry_ref + risk_scaled * params.tp1_rr
        broker_tp_reported_unscaled = broker_tp_from_fixed_code / FRACTIONAL_UNIT
        broker_sl_from_fixed_code = scaled_entry_ref - risk_scaled

        lifecycle_rows.append(
            {
                "entry_time": entry_time,
                "entry_price": entry_price,
                "weekly_bias": "bull" if bool(frame.iloc[entry_bar]["weekly_bull"]) else "neutral",
                "daily_state": "bull" if bool(frame.iloc[entry_bar]["daily_bull"]) else "neutral",
                "exec_distance_atr": float(frame.iloc[entry_bar]["exec_distance_atr"]),
                "rsi": float(frame.iloc[entry_bar]["rsi"]),
                "adx": float(frame.iloc[entry_bar]["adx"]),
                "atr_ratio": float((frame.iloc[entry_bar]["atr"] / frame.iloc[entry_bar]["atr_ma"])),
                "tp1_leg_exit_time": tp1_leg["ExitTime"],
                "tp1_leg_exit_price": float(tp1_leg["ExitPrice"]),
                "tp1_leg_pnl": float(tp1_leg["PnL"]),
                "tp1_leg_tp_column": float(tp1_leg["TP"]) if pd.notna(tp1_leg["TP"]) else None,
                "runner_exit_time": runner_leg["ExitTime"],
                "runner_exit_price": float(runner_leg["ExitPrice"]),
                "runner_pnl": float(runner_leg["PnL"]),
                "tp1_theoretical_reached": tp1_theoretical,
                "tp2_theoretical_reached": tp2_theoretical,
                "runner_stop_last": float(stop_path["runner_stop_theoretical"].iloc[-1]),
                "runner_stop_max": float(stop_path["runner_stop_theoretical"].max()),
                "runner_stop_min": float(stop_path["runner_stop_theoretical"].min()),
                "runner_peak_high": float(stop_path["highest_since_entry"].max()),
                "broker_tp_from_fixed_code_unscaled": broker_tp_reported_unscaled,
                "broker_sl_from_fixed_code_unscaled": broker_sl_from_fixed_code / FRACTIONAL_UNIT,
                "broker_sl_invalid_at_entry": broker_sl_from_fixed_code <= 0,
                "legs_exit_same_time": tp1_leg["ExitTime"] == runner_leg["ExitTime"],
                "legs_exit_same_price": float(tp1_leg["ExitPrice"]) == float(runner_leg["ExitPrice"]),
            }
        )

    lifecycle_df = pd.DataFrame(lifecycle_rows).sort_values("entry_time")
    stop_path_df = pd.concat(stop_path_frames, ignore_index=True) if stop_path_frames else pd.DataFrame()

    summary_rows = []
    if not lifecycle_df.empty:
        summary_rows.append(
            {
                "metric": "starter_lifecycles",
                "value": int(len(lifecycle_df)),
            }
        )
        summary_rows.append(
            {
                "metric": "tp1_leg_profitable_exits",
                "value": int((lifecycle_df["tp1_leg_pnl"] > 0).sum()),
            }
        )
        summary_rows.append(
            {
                "metric": "runner_profitable_exits",
                "value": int((lifecycle_df["runner_pnl"] > 0).sum()),
            }
        )
        summary_rows.append(
            {
                "metric": "tp1_theoretical_reached_count",
                "value": int(lifecycle_df["tp1_theoretical_reached"].sum()),
            }
        )
        summary_rows.append(
            {
                "metric": "tp2_theoretical_reached_count",
                "value": int(lifecycle_df["tp2_theoretical_reached"].sum()),
            }
        )
        summary_rows.append(
            {
                "metric": "legs_exit_same_time_count",
                "value": int(lifecycle_df["legs_exit_same_time"].sum()),
            }
        )
        summary_rows.append(
            {
                "metric": "legs_exit_same_price_count",
                "value": int(lifecycle_df["legs_exit_same_price"].sum()),
            }
        )
        summary_rows.append(
            {
                "metric": "tp1_leg_tp_column_median",
                "value": float(lifecycle_df["tp1_leg_tp_column"].median()),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    lifecycle_path = paths.output_dir / f"{args.prefix}.runner_lifecycle_summary.csv"
    stop_path_path = paths.output_dir / f"{args.prefix}.runner_stop_path.csv"
    summary_path = paths.output_dir / f"{args.prefix}.runner_analysis_summary.csv"

    lifecycle_df.to_csv(lifecycle_path, index=False)
    stop_path_df.to_csv(stop_path_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Saved {lifecycle_path}")
    print(f"Saved {stop_path_path}")
    print(f"Saved {summary_path}")
    if not lifecycle_df.empty:
        print(lifecycle_df.to_string(index=False))
    if not summary_df.empty:
        print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
