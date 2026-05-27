from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from btc_signal.config import BtcSignalConfig
from btc_signal.features import make_signal_feature_frame
from btc_signal.models import PaperState
from btc_signal.risk_engine import assess_risk
from btc_signal.signal_engine import evaluate_feature_frame


def _signal_and_frame(signal: bool = True):
    cfg = BtcSignalConfig()
    frame = make_signal_feature_frame(timestamp=datetime.now(timezone.utc), signal=signal)
    return cfg, evaluate_feature_frame(frame, cfg), frame


def test_missing_feature_columns_trigger_block_risk() -> None:
    cfg, decision, _ = _signal_and_frame()
    bad_frame = pd.DataFrame(
        [{"atr_ratio": 1.0}],
        index=pd.DatetimeIndex([datetime.now(timezone.utc)], name="timestamp"),
    )

    risk = assess_risk(decision, bad_frame, cfg)

    assert risk.risk_level == "BLOCK"
    assert "missing_feature_columns" in risk.risk_flags


def test_stale_data_triggers_block() -> None:
    cfg = BtcSignalConfig(stale_after_hours=8.0)
    frame = make_signal_feature_frame(timestamp=datetime.now(timezone.utc) - timedelta(days=3), signal=True)
    decision = evaluate_feature_frame(frame, cfg)

    risk = assess_risk(decision, frame, cfg)

    assert risk.risk_level == "BLOCK"
    assert "stale_data" in risk.risk_flags


def test_high_risk_detects_extreme_distance() -> None:
    cfg, decision, frame = _signal_and_frame()
    frame.loc[frame.index[-1], "exec_distance_atr"] = cfg.max_exec_distance_atr + 1.0

    risk = assess_risk(decision, frame, cfg)

    assert risk.risk_level == "HIGH"
    assert "extreme_distance_from_ema50" in risk.risk_flags


def test_paper_state_open_position_adds_duplicate_guard() -> None:
    cfg, decision, frame = _signal_and_frame()
    state = PaperState(open_position=True, position_side="LONG")

    risk = assess_risk(decision, frame, cfg, paper_state=state)

    assert risk.risk_level == "MEDIUM"
    assert "max_paper_position_already_open" in risk.risk_flags


def test_drawdown_guard_blocks() -> None:
    cfg, decision, frame = _signal_and_frame()
    state = PaperState(max_drawdown_seen=-0.25)

    risk = assess_risk(decision, frame, cfg, paper_state=state)

    assert risk.risk_level == "BLOCK"
    assert "drawdown_guard" in risk.risk_flags
