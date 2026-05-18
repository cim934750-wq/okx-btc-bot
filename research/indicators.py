from __future__ import annotations

import numpy as np
import pandas as pd

from research.data import resample_ohlcv
from research.config import StrategyParams


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / length, adjust=False).mean()


def rsi(close: pd.Series, length: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100 - (100 / (1 + rs))


def dmi_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    di_length: int,
    adx_smoothing: int,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=high.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=high.index,
    )
    atr_series = atr(high, low, close, di_length)
    plus_rma = plus_dm.ewm(alpha=1 / di_length, adjust=False).mean()
    minus_rma = minus_dm.ewm(alpha=1 / di_length, adjust=False).mean()
    plus_di = 100 * plus_rma / atr_series.replace(0.0, np.nan)
    minus_di = 100 * minus_rma / atr_series.replace(0.0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    adx = dx.ewm(alpha=1 / adx_smoothing, adjust=False).mean()
    return plus_di.fillna(0.0), minus_di.fillna(0.0), adx.fillna(0.0)


def expand_confirmed_to_4h(higher_df: pd.DataFrame, base_index: pd.DatetimeIndex) -> pd.DataFrame:
    return higher_df.shift(1).reindex(base_index, method="ffill")


def add_regime_labels(frame: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    atr_ratio = frame["atr"] / frame["atr_ma"].replace(0.0, np.nan)
    di_spread = frame["plus_di"] - frame["minus_di"]
    frame["atr_ratio"] = atr_ratio
    frame["di_spread"] = di_spread
    frame["close_ema20_gap_atr"] = ((frame["close"] - frame["ema20"]).clip(lower=0.0)) / frame["atr"].replace(0.0, np.nan)

    bull_alignment = frame["weekly_bull"] & frame["daily_bull"] & frame["exec_bull_structure"] & frame["exec_slope_up"]
    adx_rising = frame["adx"] >= frame["adx"].shift(1)
    atr_rising = frame["atr_ratio"] >= frame["atr_ratio"].shift(1)
    di_spread_rising = frame["di_spread"] >= frame["di_spread"].shift(1)
    extension_high = frame["exec_distance_atr"] >= 1.25
    thrust_hot = (frame["rsi"] >= max(params.long_rsi_min + 4, 57)) | (frame["close_ema20_gap_atr"] >= 0.75)
    weakening_energy = (
        (frame["adx"] < frame["adx"].shift(1))
        & (frame["atr_ratio"] < frame["atr_ratio"].shift(1))
        & (frame["di_spread"] <= frame["di_spread"].shift(1))
    )
    unstable_energy = (
        ((frame["adx"] < frame["adx"].shift(1)) & (frame["di_spread"] <= frame["di_spread"].shift(1)))
        | ((frame["atr_ratio"] < frame["atr_ratio"].shift(1)) & extension_high)
    )

    frame["regime_label"] = np.select(
        [
            bull_alignment & (~extension_high) & adx_rising & atr_rising & di_spread_rising,
            bull_alignment & extension_high & thrust_hot & (~weakening_energy),
            bull_alignment & weakening_energy,
            bull_alignment & unstable_energy,
        ],
        [
            "persistent_trend",
            "mature_trend",
            "weakening_trend",
            "unstable_transition",
        ],
        default="other",
    )
    return frame


def build_feature_frame(df_4h: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    frame = df_4h.copy()

    frame["ema20"] = ema(frame["close"], params.exec_fast_length)
    frame["ema50"] = ema(frame["close"], params.exec_mid_length)
    frame["ema200"] = ema(frame["close"], params.exec_slow_length)
    frame["atr"] = atr(frame["high"], frame["low"], frame["close"], params.exec_atr_length)
    frame["atr_ma"] = frame["atr"].rolling(params.exec_atr_ma_length).mean()
    frame["rsi"] = rsi(frame["close"], params.rsi_length)
    frame["cont_high"] = frame["high"].rolling(params.continuation_lookback).max().shift(1)
    frame["cont_low"] = frame["low"].rolling(params.continuation_lookback).min().shift(1)
    plus_di, minus_di, adx_val = dmi_adx(
        frame["high"],
        frame["low"],
        frame["close"],
        params.exec_di_length,
        params.exec_adx_smoothing,
    )
    frame["plus_di"] = plus_di
    frame["minus_di"] = minus_di
    frame["adx"] = adx_val

    weekly = resample_ohlcv(df_4h, "W-SUN")
    weekly["ema_fast"] = ema(weekly["close"], params.weekly_fast_length)
    weekly["ema_slow"] = ema(weekly["close"], params.weekly_slow_length)
    weekly["weekly_bull"] = (weekly["close"] > weekly["ema_slow"]) & (weekly["ema_slow"] > weekly["ema_slow"].shift(1))
    weekly["weekly_bear"] = (weekly["close"] < weekly["ema_slow"]) & (weekly["ema_slow"] < weekly["ema_slow"].shift(1))
    weekly["weekly_bull"] = weekly["weekly_bull"] & (weekly["ema_fast"] > weekly["ema_slow"])
    weekly["weekly_bear"] = weekly["weekly_bear"] & (weekly["ema_fast"] < weekly["ema_slow"])
    weekly_confirmed = expand_confirmed_to_4h(weekly[["ema_slow", "weekly_bull", "weekly_bear"]], frame.index)
    frame["weekly_ema200"] = weekly_confirmed["ema_slow"]
    frame["weekly_bull"] = weekly_confirmed["weekly_bull"].fillna(False)
    frame["weekly_bear"] = weekly_confirmed["weekly_bear"].fillna(False)

    daily = resample_ohlcv(df_4h, "1D")
    daily["ema20"] = ema(daily["close"], params.daily_fast_length)
    daily["ema50"] = ema(daily["close"], params.daily_mid_length)
    daily["ema200"] = ema(daily["close"], params.daily_slow_length)
    daily["atr"] = atr(daily["high"], daily["low"], daily["close"], params.daily_atr_length)
    daily["atr_ma"] = daily["atr"].rolling(params.daily_atr_ma_length).mean()
    d_plus, d_minus, d_adx = dmi_adx(
        daily["high"],
        daily["low"],
        daily["close"],
        params.daily_di_length,
        params.daily_adx_smoothing,
    )
    daily["plus_di"] = d_plus
    daily["minus_di"] = d_minus
    daily["adx"] = d_adx
    daily["bull"] = (
        (daily["close"] > daily["ema200"])
        & (daily["ema20"] > daily["ema50"])
        & (daily["ema200"] > daily["ema200"].shift(params.daily_slope_lookback))
        & (daily["plus_di"] >= daily["minus_di"])
    )
    daily["bear"] = (
        (daily["close"] < daily["ema200"])
        & (daily["ema20"] < daily["ema50"])
        & (daily["ema200"] < daily["ema200"].shift(params.daily_slope_lookback))
        & (daily["minus_di"] >= daily["plus_di"])
    )
    if params.use_daily_adx_filter:
        daily["bull"] &= daily["adx"] >= params.min_daily_adx
        daily["bear"] &= daily["adx"] >= params.min_daily_adx
    if params.use_daily_atr_expansion:
        atr_ok = daily["atr"] >= daily["atr_ma"] * params.min_daily_atr_ratio
        daily["bull"] &= atr_ok
        daily["bear"] &= atr_ok

    daily_confirmed = expand_confirmed_to_4h(daily[["ema200", "bull", "bear"]], frame.index)
    frame["daily_ema200"] = daily_confirmed["ema200"]
    frame["daily_bull"] = daily_confirmed["bull"].fillna(False)
    frame["daily_bear"] = daily_confirmed["bear"].fillna(False)

    frame["exec_bull_structure"] = (
        (frame["close"] > frame["ema200"])
        & (frame["ema20"] > frame["ema50"])
        & (frame["ema50"] > frame["ema200"])
    )
    frame["exec_bear_structure"] = (
        (frame["close"] < frame["ema200"])
        & (frame["ema20"] < frame["ema50"])
        & (frame["ema50"] < frame["ema200"])
    )
    frame["exec_slope_up"] = frame["ema50"] >= frame["ema50"].shift(params.exec_slope_lookback)
    frame["exec_slope_down"] = frame["ema50"] <= frame["ema50"].shift(params.exec_slope_lookback)
    frame["exec_adx_pass"] = frame["adx"] >= params.min_exec_adx
    frame["exec_atr_pass"] = frame["atr"] >= frame["atr_ma"] * params.min_exec_atr_ratio
    frame["exec_distance_atr"] = (frame["close"] - frame["ema50"]).abs() / frame["atr"].replace(0.0, np.nan)
    frame["exec_distance_pass"] = frame["exec_distance_atr"] >= params.min_ema_distance_atr
    frame["long_distance_cap_pass"] = (
        (not params.use_long_distance_cap)
        | (frame["exec_distance_atr"] <= params.max_long_distance_atr)
    )
    frame["short_distance_cap_pass"] = (
        (not params.use_short_distance_cap)
        | (frame["exec_distance_atr"] <= params.max_short_distance_atr)
    )
    frame["short_ema20_gap_atr"] = (frame["ema20"] - frame["close"]).clip(lower=0.0) / frame["atr"].replace(0.0, np.nan)
    frame["short_ema20_proximity_pass"] = (
        (not params.use_short_ema20_proximity_filter)
        | (frame["short_ema20_gap_atr"] <= params.max_short_ema20_gap_atr)
    )
    frame["exec_bull_momentum"] = (frame["plus_di"] >= frame["minus_di"]) & (frame["rsi"] >= params.long_rsi_min)
    frame["exec_bear_momentum"] = (frame["minus_di"] >= frame["plus_di"]) & (frame["rsi"] <= params.short_rsi_max)
    frame["short_squeeze_risk"] = (
        (frame["rsi"] >= params.short_squeeze_rsi_threshold)
        & ((frame["rsi"] - frame["rsi"].shift(1)) >= params.short_squeeze_rsi_rebound_delta)
        & (frame["minus_di"] <= frame["minus_di"].shift(1))
    )
    if params.short_squeeze_require_falling_adx:
        frame["short_squeeze_risk"] = frame["short_squeeze_risk"] & (frame["adx"] < frame["adx"].shift(1))
    frame["short_squeeze_pass"] = (not params.use_short_squeeze_filter) | (~frame["short_squeeze_risk"].fillna(False))

    frame["long_pullback"] = (
        (frame["low"] <= frame["ema20"])
        & (frame["low"] >= (frame["ema50"] - frame["atr"] * params.pullback_overshoot_atr))
        & (frame["close"] >= frame["ema50"])
    )
    frame["short_pullback"] = (
        (frame["high"] >= frame["ema20"])
        & (frame["high"] <= (frame["ema50"] + frame["atr"] * params.pullback_overshoot_atr))
        & (frame["close"] <= frame["ema50"])
    )

    frame["long_resumption_soft"] = (frame["close"] > frame["open"]) & (frame["close"] >= frame["ema20"])
    frame["short_resumption_soft"] = (frame["close"] < frame["open"]) & (frame["close"] <= frame["ema20"])
    frame["long_resumption_strong"] = frame["long_resumption_soft"] & (frame["close"] > frame["high"].shift(1))
    frame["short_resumption_strong"] = frame["short_resumption_soft"] & (frame["close"] < frame["low"].shift(1))
    frame["long_resumption"] = frame["long_resumption_strong"] if params.require_strong_resumption else frame["long_resumption_soft"]
    frame["short_resumption"] = frame["short_resumption_strong"] if params.require_strong_resumption else frame["short_resumption_soft"]

    frame["starter_long_signal"] = (
        frame["weekly_bull"]
        & frame["daily_bull"]
        & frame["exec_bull_structure"]
        & frame["exec_slope_up"]
        & frame["exec_adx_pass"]
        & frame["exec_atr_pass"]
        & frame["exec_distance_pass"]
        & frame["long_distance_cap_pass"]
        & frame["exec_bull_momentum"]
        & frame["long_pullback"]
        & frame["long_resumption"]
    )
    frame["starter_short_signal"] = (
        frame["weekly_bear"]
        & frame["daily_bear"]
        & frame["exec_bear_structure"]
        & frame["exec_slope_down"]
        & frame["exec_adx_pass"]
        & frame["exec_atr_pass"]
        & frame["exec_distance_pass"]
        & frame["short_distance_cap_pass"]
        & frame["short_ema20_proximity_pass"]
        & frame["exec_bear_momentum"]
        & frame["short_squeeze_pass"]
        & frame["short_pullback"]
        & frame["short_resumption"]
    )
    frame["add_long_signal"] = (
        frame["daily_bull"]
        & frame["exec_bull_structure"]
        & frame["exec_slope_up"]
        & frame["exec_adx_pass"]
        & frame["long_distance_cap_pass"]
        & frame["exec_bull_momentum"]
        & (frame["close"] > frame["cont_high"])
        & (frame["close"] > frame["open"])
        & (frame["adx"] >= frame["adx"].shift(1))
        & (frame["plus_di"] >= frame["plus_di"].shift(1))
    )
    frame["add_short_signal"] = (
        frame["daily_bear"]
        & frame["exec_bear_structure"]
        & frame["exec_slope_down"]
        & frame["exec_adx_pass"]
        & frame["short_distance_cap_pass"]
        & frame["short_ema20_proximity_pass"]
        & frame["exec_bear_momentum"]
        & frame["short_squeeze_pass"]
        & (frame["close"] < frame["cont_low"])
        & (frame["close"] < frame["open"])
        & (frame["adx"] >= frame["adx"].shift(1))
        & (frame["minus_di"] >= frame["minus_di"].shift(1))
    )
    frame = add_regime_labels(frame, params)
    return frame.dropna().copy()
