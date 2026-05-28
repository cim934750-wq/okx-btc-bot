from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from btc_signal.config import BtcSignalConfig
from btc_signal.data_refresh import (
    CSV_COLUMNS,
    merge_ohlcv_frames,
    normalize_ohlcv_frame,
    okx_rows_to_ohlcv_frame,
    refresh_btcusdt_4h_csv,
    validate_ohlcv_frame,
)
from btc_signal.features import make_signal_feature_frame
from btc_signal.risk_engine import assess_risk
from btc_signal.signal_engine import evaluate_feature_frame


def _ms(timestamp: str) -> str:
    return str(int(pd.Timestamp(timestamp).timestamp() * 1000))


def test_validate_ohlcv_frame_requires_expected_schema() -> None:
    bad = pd.DataFrame([{"timestamp": "2026-05-27T00:00:00+00:00", "open": 1.0}])

    with pytest.raises(ValueError, match="missing required columns"):
        validate_ohlcv_frame(bad)


def test_normalize_ohlcv_frame_sorts_and_deduplicates() -> None:
    raw = pd.DataFrame(
        [
            {
                "timestamp": "2026-05-27T04:00:00+00:00",
                "open": 2,
                "high": 3,
                "low": 1,
                "close": 2,
                "volume": 10,
            },
            {
                "timestamp": "2026-05-27T00:00:00+00:00",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 2,
                "volume": 9,
            },
            {
                "timestamp": "2026-05-27T04:00:00+00:00",
                "open": 4,
                "high": 5,
                "low": 3,
                "close": 4,
                "volume": 11,
            },
        ]
    )

    normalized, duplicates = normalize_ohlcv_frame(raw)

    assert list(normalized.columns) == list(CSV_COLUMNS)
    assert duplicates == 1
    assert list(normalized["timestamp"]) == [
        "2026-05-27T00:00:00+00:00",
        "2026-05-27T04:00:00+00:00",
    ]
    assert float(normalized["open"].iloc[-1]) == 4.0


def test_okx_rows_to_ohlcv_frame_excludes_incomplete_candle() -> None:
    rows = [
        [_ms("2026-05-27T08:00:00+00:00"), "100", "110", "90", "105", "12", "0", "0", "0"],
        [_ms("2026-05-27T04:00:00+00:00"), "90", "101", "89", "100", "10", "0", "0", "1"],
    ]

    frame, incomplete = okx_rows_to_ohlcv_frame(rows)

    assert incomplete == 1
    assert len(frame) == 1
    assert frame["timestamp"].iloc[0] == "2026-05-27T04:00:00+00:00"


def test_merge_ohlcv_frames_preserves_schema_and_replaces_duplicate() -> None:
    existing = pd.DataFrame(
        [
            {
                "timestamp": "2026-05-27T00:00:00+00:00",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 2,
                "volume": 5,
            }
        ]
    )
    fetched = pd.DataFrame(
        [
            {
                "timestamp": "2026-05-27T00:00:00+00:00",
                "open": 2,
                "high": 3,
                "low": 1,
                "close": 2.5,
                "volume": 6,
            },
            {
                "timestamp": "2026-05-27T04:00:00+00:00",
                "open": 2.5,
                "high": 4,
                "low": 2,
                "close": 3.5,
                "volume": 7,
            },
        ]
    )

    merged, duplicates = merge_ohlcv_frames(existing, fetched)

    assert duplicates == 1
    assert list(merged.columns) == list(CSV_COLUMNS)
    assert len(merged) == 2
    assert float(merged["open"].iloc[0]) == 2.0


def test_refresh_btcusdt_4h_csv_writes_report_and_csv(tmp_path, monkeypatch) -> None:
    output = tmp_path / "BTCUSDT_4h.csv"
    report_path = tmp_path / "refresh_report.json"
    pd.DataFrame(
        [
            {
                "timestamp": "2026-05-27T00:00:00+00:00",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1.5,
                "volume": 5,
            }
        ]
    ).to_csv(output, index=False)

    def fake_fetch(**_kwargs):
        return (
            [
                [_ms("2026-05-27T08:00:00+00:00"), "3", "4", "2", "3.5", "8", "0", "0", "0"],
                [_ms("2026-05-27T04:00:00+00:00"), "2", "3", "1", "2.5", "7", "0", "0", "1"],
            ],
            "https://www.okx.com/public-test",
        )

    monkeypatch.setattr("btc_signal.data_refresh.fetch_okx_public_candles", fake_fetch)

    report = refresh_btcusdt_4h_csv(output_path=output, report_path=report_path)
    refreshed = pd.read_csv(output)

    assert report.old_rows == 1
    assert report.new_rows == 2
    assert report.incomplete_rows_excluded == 1
    assert report.new_latest_timestamp == "2026-05-27T04:00:00+00:00"
    assert report_path.exists()
    assert list(refreshed.columns) == list(CSV_COLUMNS)


def test_recent_refreshed_timestamp_does_not_trigger_stale_risk() -> None:
    cfg = BtcSignalConfig(stale_after_hours=8.0)
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    frame = make_signal_feature_frame(timestamp=datetime(2026, 5, 27, 8, 0, tzinfo=timezone.utc), signal=True)
    decision = evaluate_feature_frame(frame, cfg)

    risk = assess_risk(decision, frame, cfg, now=now)

    assert "stale_data" not in risk.risk_flags
