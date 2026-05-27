from __future__ import annotations

from btc_signal.models import PaperState, ResponseAction, ResponseDecision, RiskAssessment, SignalDecision


LIVE_TRADING_ACTIONS = {"LIVE_BUY", "LIVE_SELL", "MARKET_BUY", "MARKET_SELL"}
ALLOWED_ACTIONS = {action.value for action in ResponseAction}


def decide_response(
    signal: SignalDecision,
    risk: RiskAssessment,
    paper_state: PaperState | None = None,
) -> ResponseDecision:
    risk_flags = set(risk.risk_flags)

    if signal.decision == "BLOCKED" or risk.risk_level == "BLOCK":
        return _safe_response(
            ResponseDecision(
                action=ResponseAction.BLOCK.value,
                reason=risk.blocked_reason or signal.reasoning_summary,
                required_user_action="Review blocked data/risk condition before rerunning paper automation.",
                should_log=True,
                should_notify=True,
            )
        )

    if paper_state is not None and paper_state.open_position:
        if risk.risk_level == "HIGH":
            return _safe_response(
                ResponseDecision(
                    action=ResponseAction.EXIT_WARNING.value,
                    reason="Paper position is open while high risk flags are active: " + ", ".join(sorted(risk_flags)),
                    required_user_action="Review the paper position manually; no live order will be placed.",
                    should_log=True,
                    should_notify=True,
                )
            )
        return _safe_response(
            ResponseDecision(
                action=ResponseAction.WATCH.value,
                reason="Paper position already open; duplicate PAPER_LONG is disabled.",
                required_user_action=None,
                should_log=True,
                should_notify=False,
            )
        )

    if signal.decision != "LONG_SIGNAL":
        if risk.risk_level in {"MEDIUM", "HIGH"} or signal.decision == "WATCH":
            return _safe_response(
                ResponseDecision(
                    action=ResponseAction.WATCH.value,
                    reason="No Long1 paper entry. Conditions are near-candidate or risk warnings are present.",
                    required_user_action=None,
                    should_log=True,
                    should_notify=False,
                )
            )
        return _safe_response(
            ResponseDecision(
                action=ResponseAction.WAIT.value,
                reason="No Long1 signal on the latest completed 4h candle.",
                required_user_action=None,
                should_log=True,
                should_notify=False,
            )
        )

    if risk.risk_level in {"LOW", "MEDIUM"}:
        return _safe_response(
            ResponseDecision(
                action=ResponseAction.PAPER_LONG.value,
                reason="Long1 signal passed and risk is not blocking; record paper entry only.",
                required_user_action=None,
                should_log=True,
                should_notify=True,
            )
        )

    return _safe_response(
        ResponseDecision(
            action=ResponseAction.BLOCK.value,
            reason="Long1 signal exists, but high risk flags block paper entry: " + ", ".join(sorted(risk_flags)),
            required_user_action="Review risk warnings before allowing another paper signal.",
            should_log=True,
            should_notify=True,
        )
    )


def _safe_response(response: ResponseDecision) -> ResponseDecision:
    if response.action in LIVE_TRADING_ACTIONS or response.action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unsafe response action blocked: {response.action}")
    return response
