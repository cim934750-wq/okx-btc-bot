from __future__ import annotations

from datetime import datetime, timezone

from btc_signal.config import BtcSignalConfig
from btc_signal.features import make_signal_feature_frame
from btc_signal.models import PaperState, RiskAssessment
from btc_signal.response_engine import ALLOWED_ACTIONS, decide_response
from btc_signal.risk_engine import assess_risk
from btc_signal.signal_engine import evaluate_feature_frame


def _decision(signal: bool = True):
    cfg = BtcSignalConfig()
    frame = make_signal_feature_frame(timestamp=datetime.now(timezone.utc), signal=signal)
    decision = evaluate_feature_frame(frame, cfg)
    return cfg, decision, frame


def test_long_signal_low_risk_returns_paper_long() -> None:
    cfg, decision, frame = _decision(signal=True)
    risk = assess_risk(decision, frame, cfg)

    response = decide_response(decision, risk)

    assert response.action == "PAPER_LONG"


def test_long_signal_high_risk_returns_block() -> None:
    _, decision, _ = _decision(signal=True)
    risk = RiskAssessment(risk_level="HIGH", risk_flags=["extreme_distance_from_ema50"])

    response = decide_response(decision, risk)

    assert response.action == "BLOCK"


def test_no_signal_returns_wait_or_watch() -> None:
    cfg, decision, frame = _decision(signal=False)
    risk = assess_risk(decision, frame, cfg)

    response = decide_response(decision, risk)

    assert response.action in {"WAIT", "WATCH"}


def test_paper_state_prevents_duplicate_open_paper_long() -> None:
    cfg, decision, frame = _decision(signal=True)
    state = PaperState(open_position=True, position_side="LONG")
    risk = assess_risk(decision, frame, cfg, paper_state=state)

    response = decide_response(decision, risk, paper_state=state)

    assert response.action in {"WATCH", "BLOCK", "EXIT_WARNING"}
    assert response.action != "PAPER_LONG"


def test_response_engine_never_returns_live_trading_action() -> None:
    cfg, long_decision, frame = _decision(signal=True)
    low_risk = assess_risk(long_decision, frame, cfg)
    high_risk = RiskAssessment(risk_level="HIGH", risk_flags=["sudden_volatility_expansion"])
    block_risk = RiskAssessment(risk_level="BLOCK", risk_flags=["stale_data"], blocked_reason="stale")
    _, no_signal_decision, no_signal_frame = _decision(signal=False)
    no_signal_risk = assess_risk(no_signal_decision, no_signal_frame, cfg)

    responses = [
        decide_response(long_decision, low_risk),
        decide_response(long_decision, high_risk),
        decide_response(long_decision, block_risk),
        decide_response(no_signal_decision, no_signal_risk),
        decide_response(long_decision, low_risk, paper_state=PaperState(open_position=True)),
    ]

    for response in responses:
        assert response.action in ALLOWED_ACTIONS
        assert not response.action.startswith("LIVE")
        assert response.action not in {"LIVE_BUY", "LIVE_SELL", "MARKET_BUY", "MARKET_SELL"}
