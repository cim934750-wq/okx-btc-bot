from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from btc_signal.config import BtcSignalConfig
from btc_signal.features import make_signal_feature_frame
from btc_signal.signal_engine import evaluate_feature_frame


def test_signal_engine_returns_structured_long_decision_on_synthetic_feature_frame() -> None:
    cfg = BtcSignalConfig()
    frame = make_signal_feature_frame(timestamp=datetime.now(timezone.utc), signal=True)

    decision = evaluate_feature_frame(frame, cfg)

    assert decision.symbol == "BTCUSDT"
    assert decision.timeframe == "4h"
    assert decision.decision == "LONG_SIGNAL"
    assert decision.signal_name == "Long1"
    assert decision.confidence_label == "strong"
    assert decision.missing_conditions == []
    assert "weekly_bull" in decision.evidence
    assert "exec_distance_atr" in decision.evidence


def test_signal_engine_returns_wait_when_no_signal() -> None:
    cfg = BtcSignalConfig()
    frame = make_signal_feature_frame(timestamp=datetime.now(timezone.utc), signal=False)

    decision = evaluate_feature_frame(frame, cfg)

    assert decision.decision in {"WAIT", "WATCH"}
    assert decision.signal_name is None
    assert "long_pullback" in decision.missing_conditions


def test_missing_feature_columns_trigger_blocked_signal_decision() -> None:
    cfg = BtcSignalConfig()
    frame = pd.DataFrame(
        [{"weekly_bull": True, "daily_bull": True}],
        index=pd.DatetimeIndex([datetime.now(timezone.utc)], name="timestamp"),
    )

    decision = evaluate_feature_frame(frame, cfg)

    assert decision.decision == "BLOCKED"
    assert "starter_long_signal" in decision.missing_conditions
    assert decision.confidence_label == "none"
