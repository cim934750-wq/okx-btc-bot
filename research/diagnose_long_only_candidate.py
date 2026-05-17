from __future__ import annotations

import argparse

import pandas as pd

from research.config import Paths
from research.data import load_ohlcv_csv
from research.indicators import build_feature_frame
from research.long_only_candidate import (
    long_only_backtest_config,
    long_only_production_params,
    long_only_production_params_with_fix,
)
from research.strategy import run_backtest


SEGMENT_START = "2025-01-01"
SEGMENT_END = "2026-04-12 23:59:59"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose weak long-only segment.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long_only_2025_2026")
    parser.add_argument("--with-fix", action="store_true")
    return parser.parse_args()


def slice_frame(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    return df[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index <= pd.Timestamp(end, tz="UTC"))].copy()


def inspect_long_trade(
    frame: pd.DataFrame,
    trade: pd.Series,
    stop_mult: float,
    tp1_rr: float,
    tp2_rr: float,
    trail_mult: float,
    be_offset_atr: float,
    tp1_profit_lock_atr: float,
    tp2_profit_lock_rr: float,
    tp2_trail_atr_mult: float,
    commission_rate: float,
) -> dict:
    entry_bar = int(trade["EntryBar"])
    exit_bar = int(trade["ExitBar"])
    entry_idx = frame.index[entry_bar]
    sub = frame.iloc[entry_bar : exit_bar + 1].copy()
    entry_price = float(trade["EntryPrice"])
    exit_price = float(trade["ExitPrice"])

    tp1_hit = False
    tp2_hit = False
    highest = float(sub["high"].iloc[0])
    trailing_active = False
    trailing_stop_at_exit = None
    stop_price_at_exit = None
    exit_reason = "unknown"
    tp1_floor_at_exit = None
    tp2_floor_at_exit = None

    for _, row in sub.iterrows():
        atr = float(row["atr"])
        risk = atr * stop_mult
        base_stop = entry_price - risk
        tp1 = entry_price + risk * tp1_rr
        tp2 = entry_price + risk * tp2_rr
        round_trip_fee_buffer = entry_price * commission_rate * 2.0
        highest = max(highest, float(row["high"]))
        if (not tp1_hit) and float(row["high"]) >= tp1:
            tp1_hit = True
        if float(row["high"]) >= tp2:
            tp2_hit = True
        tp1_floor = entry_price + round_trip_fee_buffer + atr * be_offset_atr
        if tp1_profit_lock_atr > 0:
            tp1_floor = max(tp1_floor, entry_price + round_trip_fee_buffer + atr * tp1_profit_lock_atr)
        break_even = tp1_floor if tp1_hit else base_stop
        active_trail_mult = tp2_trail_atr_mult if (tp2_hit and tp2_trail_atr_mult > 0) else trail_mult
        trail_raw = highest - atr * active_trail_mult
        runner_stop = max(break_even, trail_raw)
        tp2_floor = None
        if tp2_hit and tp2_profit_lock_rr > 0:
            tp2_floor = entry_price + round_trip_fee_buffer + risk * tp2_profit_lock_rr
            runner_stop = max(runner_stop, tp2_floor)
        trailing_active = trailing_active or (runner_stop > base_stop + 1e-9)

        stop_price_at_exit = base_stop
        trailing_stop_at_exit = runner_stop
        tp1_floor_at_exit = tp1_floor
        tp2_floor_at_exit = tp2_floor

    exit_row = sub.iloc[-1]
    exit_low = float(exit_row["low"])
    exit_high = float(exit_row["high"])
    exit_close = float(exit_row["close"])
    trend_fail = (exit_close < float(exit_row["ema50"]) and float(exit_row["minus_di"]) > float(exit_row["plus_di"])) or (not bool(exit_row["weekly_bull"])) or (not bool(exit_row["daily_bull"]))

    if tp2_hit and exit_price >= entry_price:
        exit_reason = "tp2_or_runner_takeprofit"
    elif trailing_stop_at_exit is not None and exit_low <= trailing_stop_at_exit:
        exit_reason = "trailing_or_stop_exit"
    elif trend_fail:
        exit_reason = "trend_fail_exit"

    return {
        "tag": trade["Tag"],
        "entry_timestamp": trade["EntryTime"],
        "exit_timestamp": trade["ExitTime"],
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_price_at_exit": stop_price_at_exit,
        "trailing_stop_at_exit": trailing_stop_at_exit,
        "tp1_floor_at_exit": tp1_floor_at_exit,
        "tp2_floor_at_exit": tp2_floor_at_exit,
        "tp1_hit": tp1_hit,
        "tp2_hit": tp2_hit,
        "trailing_active": trailing_active,
        "exit_bar_high": exit_high,
        "exit_bar_low": exit_low,
        "same_bar_tp1_touch": exit_high >= (entry_price + float(sub["atr"].iloc[-1]) * tp1_rr * stop_mult),
        "same_bar_tp2_touch": exit_high >= (entry_price + float(sub["atr"].iloc[-1]) * tp2_rr * stop_mult),
        "weekly_bias": "bull" if bool(sub["weekly_bull"].iloc[0]) else "neutral",
        "daily_state": "bull" if bool(sub["daily_bull"].iloc[0]) else "neutral",
        "exec_distance_atr": float(sub["exec_distance_atr"].iloc[0]),
        "rsi": float(sub["rsi"].iloc[0]),
        "adx": float(sub["adx"].iloc[0]),
        "atr_ratio": float((sub["atr"] / sub["atr_ma"]).iloc[0]),
        "pnl": float(trade["PnL"]),
        "return_pct": float(trade["ReturnPct"]),
        "held_bars": exit_bar - entry_bar,
        "exit_reason": exit_reason,
    }


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    segment_df = slice_frame(raw_df, SEGMENT_START, SEGMENT_END)
    params = long_only_production_params_with_fix() if args.with_fix else long_only_production_params()
    bt_config = long_only_backtest_config()

    stats, trades = run_backtest(segment_df, params, bt_config)
    frame = build_feature_frame(segment_df, params)

    loss_trades = trades[trades["PnL"] <= 0].copy()
    details = []
    for _, trade in loss_trades.iterrows():
        details.append(
            inspect_long_trade(
                frame,
                trade,
                params.stop_atr_mult,
                params.tp1_rr,
                params.tp2_rr,
                params.trail_atr_mult,
                params.breakeven_offset_atr,
                params.long_tp1_profit_lock_atr,
                params.long_tp2_profit_lock_rr,
                params.long_tp2_trail_atr_mult,
                bt_config.commission,
            )
        )

    details_df = pd.DataFrame(details).sort_values("entry_timestamp")
    out_path = paths.output_dir / f"{args.prefix}.loss_diagnosis.csv"
    details_df.to_csv(out_path, index=False)
    print(f"Saved {out_path}")
    if not details_df.empty:
        print(details_df.to_string(index=False))


if __name__ == "__main__":
    main()
