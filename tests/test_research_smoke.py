import numpy as np
import pandas as pd

from research.config import StrategyParams
from research.indicators import build_feature_frame


def _synthetic_ohlcv(rows: int = 720) -> pd.DataFrame:
    index = pd.date_range("2023-01-01", periods=rows, freq="4h", tz="UTC")
    base = np.linspace(20_000.0, 24_000.0, rows)
    wave = np.sin(np.linspace(0.0, 18.0, rows)) * 250.0
    close = base + wave
    open_ = close + np.cos(np.linspace(0.0, 18.0, rows)) * 20.0
    high = np.maximum(open_, close) + 75.0
    low = np.minimum(open_, close) - 75.0
    volume = np.full(rows, 100.0)

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


def test_feature_frame_smoke_produces_required_columns() -> None:
    frame = build_feature_frame(_synthetic_ohlcv(), StrategyParams())

    expected_columns = {
        "ema20",
        "ema50",
        "atr",
        "starter_long_signal",
        "starter_short_signal",
        "add_long_signal",
        "add_short_signal",
    }

    assert not frame.empty
    assert expected_columns.issubset(frame.columns)
