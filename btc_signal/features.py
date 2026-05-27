from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from research.config import StrategyParams
from research.data import REQUIRED_COLUMNS, load_ohlcv_csv
from research.indicators import build_feature_frame


LONG1_CONDITION_COLUMNS: tuple[str, ...] = (
    "weekly_bull",
    "daily_bull",
    "exec_bull_structure",
    "exec_slope_up",
    "exec_adx_pass",
    "exec_atr_pass",
    "exec_distance_pass",
    "exec_bull_momentum",
    "long_pullback",
    "long_resumption",
)

EVIDENCE_FIELDS: tuple[str, ...] = (
    "weekly_bull",
    "daily_bull",
    "exec_bull_structure",
    "exec_slope_up",
    "exec_adx_pass",
    "exec_atr_pass",
    "exec_distance_pass",
    "exec_bull_momentum",
    "long_pullback",
    "long_resumption",
    "rsi",
    "adx",
    "atr_ratio",
    "ema20",
    "ema50",
    "ema200",
    "close",
    "exec_distance_atr",
)

RISK_FEATURE_COLUMNS: tuple[str, ...] = (
    "atr",
    "atr_ratio",
    "close",
    "ema50",
    "exec_distance_atr",
    "weekly_bull",
    "daily_bull",
)

REQUIRED_FEATURE_COLUMNS: tuple[str, ...] = (
    *LONG1_CONDITION_COLUMNS,
    *EVIDENCE_FIELDS,
    *RISK_FEATURE_COLUMNS,
    "starter_long_signal",
)


def load_btc_4h_csv(path: str) -> pd.DataFrame:
    return load_ohlcv_csv(path)


def build_long1_feature_frame(df_4h: pd.DataFrame, params: StrategyParams | None = None) -> pd.DataFrame:
    return build_feature_frame(df_4h, params or StrategyParams())


def missing_feature_columns(frame: pd.DataFrame, required: tuple[str, ...] = REQUIRED_FEATURE_COLUMNS) -> list[str]:
    return sorted({column for column in required if column not in frame.columns})


def make_synthetic_ohlcv(rows: int = 900, end: datetime | None = None) -> pd.DataFrame:
    end_time = end or datetime.now(timezone.utc)
    end_time = end_time.replace(minute=0, second=0, microsecond=0)
    end_time = end_time - timedelta(hours=end_time.hour % 4)
    index = pd.date_range(end=end_time, periods=rows, freq="4h", tz="UTC")

    trend = np.linspace(40_000.0, 72_000.0, rows)
    wave = np.sin(np.linspace(0.0, 18.0, rows)) * 900.0
    close = trend + wave
    open_ = close - np.cos(np.linspace(0.0, 15.0, rows)) * 120.0
    high = np.maximum(open_, close) + 250.0
    low = np.minimum(open_, close) - 250.0
    volume = np.full(rows, 1_000.0)

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def make_signal_feature_frame(timestamp: datetime | None = None, signal: bool = True) -> pd.DataFrame:
    ts = timestamp or datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    data = {
        "weekly_bull": True,
        "daily_bull": True,
        "exec_bull_structure": True,
        "exec_slope_up": True,
        "exec_adx_pass": True,
        "exec_atr_pass": True,
        "exec_distance_pass": True,
        "exec_bull_momentum": True,
        "long_pullback": True,
        "long_resumption": True,
        "starter_long_signal": signal,
        "rsi": 58.0,
        "adx": 22.0,
        "atr": 900.0,
        "atr_ratio": 1.05,
        "ema20": 70_500.0,
        "ema50": 70_000.0,
        "ema200": 65_000.0,
        "close": 70_850.0,
        "exec_distance_atr": 0.94,
    }
    if not signal:
        data["long_pullback"] = False
        data["starter_long_signal"] = False
    return pd.DataFrame([data], index=pd.DatetimeIndex([ts], name="timestamp"))
