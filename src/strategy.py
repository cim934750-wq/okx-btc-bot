from __future__ import annotations

from typing import Any

import pandas as pd


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ema20"] = result["close"].ewm(span=20, adjust=False).mean()
    result["ema60"] = result["close"].ewm(span=60, adjust=False).mean()
    result["ema200"] = result["close"].ewm(span=200, adjust=False).mean()
    result["rsi14"] = _rsi(result["close"], period=14)
    result["atr14"] = _atr(result, period=14)
    return result


def _rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = average_gain / average_loss
    return 100 - (100 / (1 + rs))


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    previous_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def generate_signal(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"signal": "hold", "reason": "no_data"}

    latest = df.iloc[-1]
    required = ["close", "ema20", "ema60", "ema200", "rsi14", "atr14"]
    if latest[required].isna().any():
        return {
            "signal": "hold",
            "timestamp": latest["timestamp"],
            "close": float(latest["close"]),
            "reason": "indicators_not_ready",
        }

    close = float(latest["close"])
    ema20 = float(latest["ema20"])
    ema60 = float(latest["ema60"])
    ema200 = float(latest["ema200"])
    rsi14 = float(latest["rsi14"])
    atr14 = float(latest["atr14"])

    if close < ema20:
        signal = "exit"
        reason = "close_below_ema20"
    elif close > ema200 and ema20 > ema60 and 45 <= rsi14 <= 70:
        signal = "long_entry"
        reason = "trend_alignment_rsi_filter"
    else:
        signal = "hold"
        reason = "conditions_not_met"

    return {
        "signal": signal,
        "timestamp": latest["timestamp"],
        "close": close,
        "ema20": ema20,
        "ema60": ema60,
        "ema200": ema200,
        "rsi14": rsi14,
        "atr14": atr14,
        "reason": reason,
    }


def add_signal_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = calculate_indicators(df)
    result["long_entry"] = (
        (result["close"] > result["ema200"])
        & (result["ema20"] > result["ema60"])
        & (result["rsi14"].between(45, 70))
    )
    result["exit"] = result["close"] < result["ema20"]
    return result
