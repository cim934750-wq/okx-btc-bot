from __future__ import annotations

import json
import warnings as warnings_module
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from btc_signal.config import BtcSignalConfig
from btc_signal.data_refresh import FOUR_HOURS, normalize_ohlcv_frame, read_existing_csv
from btc_signal.models import PaperState, ResponseDecision, RiskAssessment, SignalDecision, to_jsonable
from btc_signal.monitoring import MonitoringReport, build_monitoring_report, report_to_dict as monitoring_to_dict
from btc_signal.response_engine import decide_response
from btc_signal.risk_engine import assess_risk
from btc_signal.signal_engine import generate_signal


@dataclass(slots=True)
class PaperStatusReport:
    generated_at: str
    mode: str
    safety: dict[str, Any]
    data: dict[str, Any]
    latest_signal: dict[str, Any]
    latest_risk: dict[str, Any]
    latest_response: dict[str, Any]
    monitoring: dict[str, Any]
    paper_state: dict[str, Any]
    warnings: list[str]


def _utc_now(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _utc_iso(now: datetime | None = None) -> str:
    return _utc_now(now).isoformat()


def _parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _round_hours(hours: float | None) -> float | None:
    if hours is None:
        return None
    return round(hours, 4)


def summarize_data_freshness(
    data_path: str | Path,
    config: BtcSignalConfig,
    now: datetime | None = None,
) -> tuple[dict[str, Any], list[str]]:
    path = Path(data_path)
    warnings: list[str] = []
    summary: dict[str, Any] = {
        "csv_path": str(path),
        "available": False,
        "row_count": 0,
        "latest_candle_timestamp": None,
        "latest_candle_age_hours": None,
        "latest_candle_complete": None,
        "stale_after_hours": config.stale_after_hours,
        "stale": True,
        "status": "missing",
        "validation_error": None,
    }
    if not path.exists():
        warnings.append(f"BTCUSDT 4h CSV is missing: {path}")
        return summary, warnings

    try:
        raw = read_existing_csv(path)
        normalized, duplicates_removed = normalize_ohlcv_frame(raw)
    except Exception as exc:  # noqa: BLE001 - dashboard should report bad data without crashing.
        summary["status"] = "invalid"
        summary["validation_error"] = str(exc)
        warnings.append(f"BTCUSDT 4h CSV could not be validated: {exc}")
        return summary, warnings

    summary["available"] = True
    summary["row_count"] = int(len(normalized))
    summary["duplicates_if_normalized"] = int(duplicates_removed)
    if normalized.empty:
        summary["status"] = "empty"
        warnings.append(f"BTCUSDT 4h CSV is empty: {path}")
        return summary, warnings

    latest = str(normalized["timestamp"].iloc[-1])
    latest_dt = _parse_time(latest)
    summary["latest_candle_timestamp"] = latest
    if latest_dt is None:
        summary["status"] = "invalid"
        summary["validation_error"] = "latest timestamp was not parseable"
        warnings.append(f"Latest BTCUSDT 4h timestamp was not parseable: {latest}")
        return summary, warnings

    age_hours = (_utc_now(now) - latest_dt).total_seconds() / 3600.0
    is_stale = age_hours > config.stale_after_hours
    summary["latest_candle_age_hours"] = _round_hours(age_hours)
    summary["latest_candle_complete"] = latest_dt + FOUR_HOURS <= _utc_now(now)
    summary["stale"] = bool(is_stale)
    summary["status"] = "stale" if is_stale else "fresh"
    if is_stale:
        warnings.append(
            f"Latest BTCUSDT 4h candle is {age_hours:.2f} hours old; "
            f"limit is {config.stale_after_hours:.2f} hours."
        )
    return summary, warnings


def _paper_state_summary(state: PaperState | None, source: str, available: bool) -> dict[str, Any]:
    return {
        "source": source,
        "available": available,
        "open_position": state.open_position if state is not None else None,
        "position_side": state.position_side if state is not None else None,
        "entry_time": state.entry_time if state is not None else None,
        "entry_price": state.entry_price if state is not None else None,
        "last_signal_time": state.last_signal_time if state is not None else None,
        "paper_equity": state.paper_equity if state is not None else None,
        "max_drawdown_seen": state.max_drawdown_seen if state is not None else None,
        "notes_count": len(state.notes) if state is not None else 0,
    }


def load_paper_state_read_only(path: str | Path, symbol: str = "BTCUSDT") -> tuple[PaperState | None, dict[str, Any], list[str]]:
    state_path = Path(path)
    warnings: list[str] = []
    if not state_path.exists():
        warnings.append(f"Paper state file is missing: {state_path}")
        return None, _paper_state_summary(None, str(state_path), False), warnings
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        payload.setdefault("symbol", symbol)
        payload.setdefault("notes", [])
        state = PaperState(**payload)
    except Exception as exc:  # noqa: BLE001 - status view should report malformed state.
        warnings.append(f"Paper state file could not be read: {state_path}: {exc}")
        return None, _paper_state_summary(None, str(state_path), False), warnings
    return state, _paper_state_summary(state, str(state_path), True), warnings


def _signal_summary(signal: SignalDecision | None) -> dict[str, Any]:
    if signal is None:
        return {
            "available": False,
            "timestamp": None,
            "decision": "BLOCKED",
            "long1_active": False,
            "signal_name": None,
            "confidence_label": "none",
            "passed_condition_count": 0,
            "missing_condition_count": 0,
            "main_missing_conditions": [],
            "passed_conditions": [],
            "missing_conditions": [],
            "evidence": {},
            "reasoning_summary": "Signal generation was unavailable.",
        }
    return {
        "available": True,
        "timestamp": signal.timestamp,
        "decision": signal.decision,
        "long1_active": signal.signal_name == "Long1" and signal.decision == "LONG_SIGNAL",
        "signal_name": signal.signal_name,
        "confidence_label": signal.confidence_label,
        "passed_condition_count": len(signal.passed_conditions),
        "missing_condition_count": len(signal.missing_conditions),
        "main_missing_conditions": signal.missing_conditions[:5],
        "passed_conditions": signal.passed_conditions,
        "missing_conditions": signal.missing_conditions,
        "evidence": signal.evidence,
        "reasoning_summary": signal.reasoning_summary,
    }


def _risk_summary(risk: RiskAssessment | None) -> dict[str, Any]:
    if risk is None:
        return {
            "risk_level": "BLOCK",
            "risk_flags": ["signal_unavailable"],
            "blocked_reason": "Signal or data was unavailable.",
            "warnings": ["Signal or data was unavailable."],
        }
    return {
        "risk_level": risk.risk_level,
        "risk_flags": risk.risk_flags,
        "blocked_reason": risk.blocked_reason,
        "warnings": risk.warnings,
    }


def _response_summary(response: ResponseDecision | None) -> dict[str, Any]:
    if response is None:
        return {
            "action": "BLOCK",
            "reason": "Status dashboard could not compute a response from current data.",
            "required_user_action": "Review data and signal warnings before rerunning paper automation.",
            "should_log": False,
            "should_notify": False,
        }
    return {
        "action": response.action,
        "reason": response.reason,
        "required_user_action": response.required_user_action,
        "should_log": response.should_log,
        "should_notify": response.should_notify,
    }


def _monitoring_summary(report: MonitoringReport) -> dict[str, Any]:
    payload = monitoring_to_dict(report)
    metrics = payload["metrics"]
    return {
        "total_log_entries_read": metrics["total_log_entries_read"],
        "entries_summarized": metrics["entries_summarized"],
        "signal_decision_counts": metrics["signal_decision_counts"],
        "response_action_counts": metrics["response_action_counts"],
        "risk_level_counts": metrics["risk_level_counts"],
        "stale_data_flag_count": metrics["stale_data_flag_count"],
        "top_risk_flags": metrics["top_risk_flags"],
        "latest_decision": payload["latest_decision"],
        "warnings": payload["warnings"],
        "files_read": payload["log_source"]["files_read"],
    }


def build_paper_status_report(
    *,
    config: BtcSignalConfig,
    log_path: str | Path | None = None,
    logs_dir: str | Path | None = None,
    state_path: str | Path | None = None,
    limit: int = 20,
    now: datetime | None = None,
) -> PaperStatusReport:
    current = _utc_now(now)
    warnings: list[str] = []
    data_summary, data_warnings = summarize_data_freshness(config.data_path, config, now=current)
    warnings.extend(data_warnings)

    state_target = Path(state_path) if state_path is not None else config.paper_state_path
    paper_state, paper_summary, state_warnings = load_paper_state_read_only(state_target, symbol=config.symbol)
    warnings.extend(state_warnings)

    signal: SignalDecision | None = None
    risk: RiskAssessment | None = None
    response: ResponseDecision | None = None
    if data_summary["available"] and data_summary["validation_error"] is None and data_summary["row_count"] > 0:
        try:
            with warnings_module.catch_warnings():
                warnings_module.simplefilter("ignore", FutureWarning)
                signal, feature_frame = generate_signal(config)
            risk = assess_risk(signal, feature_frame, config, paper_state=paper_state, now=current)
            response = decide_response(signal, risk, paper_state=paper_state)
        except Exception as exc:  # noqa: BLE001 - dashboard must stay inspectable on runtime errors.
            warnings.append(f"Signal/risk evaluation failed: {exc}")
    else:
        warnings.append("Signal/risk evaluation skipped because local BTCUSDT 4h data is unavailable or invalid.")

    monitoring_report = build_monitoring_report(
        log_path=log_path,
        logs_dir=logs_dir,
        state_path=state_target,
        limit=limit,
        now=current,
    )
    monitoring_summary = _monitoring_summary(monitoring_report)
    warnings.extend(monitoring_summary["warnings"])
    if risk is not None:
        warnings.extend(risk.warnings)

    # Preserve order while removing exact duplicate warning strings.
    deduped_warnings = list(dict.fromkeys(warnings))

    return PaperStatusReport(
        generated_at=_utc_iso(current),
        mode="paper_status_read_only",
        safety={
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
            "read_only_report": True,
            "refreshes_data_by_default": False,
        },
        data=data_summary,
        latest_signal=_signal_summary(signal),
        latest_risk=_risk_summary(risk),
        latest_response=_response_summary(response),
        monitoring=monitoring_summary,
        paper_state=paper_summary,
        warnings=deduped_warnings,
    )


def report_to_dict(report: PaperStatusReport) -> dict[str, Any]:
    return to_jsonable(asdict(report))


def status_json(report: PaperStatusReport) -> str:
    return json.dumps(report_to_dict(report), indent=2, sort_keys=True)


def format_text_report(report: PaperStatusReport) -> str:
    payload = report_to_dict(report)
    data = payload["data"]
    signal = payload["latest_signal"]
    risk = payload["latest_risk"]
    response = payload["latest_response"]
    monitoring = payload["monitoring"]
    paper_state = payload["paper_state"]
    lines = [
        "BTC Paper Status Dashboard",
        f"generated_at: {payload['generated_at']}",
        f"mode: {payload['mode']}",
        f"csv_path: {data['csv_path']}",
        f"row_count: {data['row_count']}",
        f"latest_candle_timestamp: {data['latest_candle_timestamp']}",
        f"latest_candle_age_hours: {data['latest_candle_age_hours']}",
        f"data_status: {data['status']}",
        f"stale: {data['stale']}",
        (
            "latest_signal: "
            f"decision={signal['decision']} long1_active={signal['long1_active']} "
            f"confidence={signal['confidence_label']}"
        ),
        (
            "long1_conditions: "
            f"passed={signal['passed_condition_count']} missing={signal['missing_condition_count']} "
            f"main_missing={signal['main_missing_conditions']}"
        ),
        f"latest_risk: level={risk['risk_level']} flags={risk['risk_flags']}",
        f"latest_response: action={response['action']} reason={response['reason']}",
        (
            "paper_state: "
            f"open_position={paper_state['open_position']} side={paper_state['position_side']} "
            f"entry_time={paper_state['entry_time']} entry_price={paper_state['entry_price']}"
        ),
        (
            "monitoring: "
            f"total={monitoring['total_log_entries_read']} summarized={monitoring['entries_summarized']} "
            f"stale_data_count={monitoring['stale_data_flag_count']}"
        ),
        f"monitoring_signal_counts: {monitoring['signal_decision_counts']}",
        f"monitoring_response_counts: {monitoring['response_action_counts']}",
        f"monitoring_risk_counts: {monitoring['risk_level_counts']}",
        f"monitoring_top_risk_flags: {monitoring['top_risk_flags']}",
        f"warnings: {payload['warnings']}",
    ]
    return "\n".join(lines) + "\n"


def format_markdown_report(report: PaperStatusReport) -> str:
    payload = report_to_dict(report)
    data = payload["data"]
    signal = payload["latest_signal"]
    risk = payload["latest_risk"]
    response = payload["latest_response"]
    monitoring = payload["monitoring"]
    paper_state = payload["paper_state"]
    lines = [
        "# BTC Paper Status Dashboard",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Read-only: `{payload['safety']['read_only_report']}`",
        f"- Live orders enabled: `{payload['safety']['live_orders_enabled']}`",
        "",
        "## Data Freshness",
        "",
        f"- CSV path: `{data['csv_path']}`",
        f"- Row count: `{data['row_count']}`",
        f"- Latest candle: `{data['latest_candle_timestamp']}`",
        f"- Latest candle age hours: `{data['latest_candle_age_hours']}`",
        f"- Status: `{data['status']}`",
        f"- Stale: `{data['stale']}`",
        "",
        "## Latest Signal",
        "",
        f"- Decision: `{signal['decision']}`",
        f"- Long1 active: `{signal['long1_active']}`",
        f"- Confidence: `{signal['confidence_label']}`",
        f"- Passed conditions: `{signal['passed_condition_count']}`",
        f"- Missing conditions: `{signal['missing_condition_count']}`",
        f"- Main missing conditions: `{signal['main_missing_conditions']}`",
        "",
        "## Risk And Response",
        "",
        f"- Risk level: `{risk['risk_level']}`",
        f"- Risk flags: `{risk['risk_flags']}`",
        f"- Response action: `{response['action']}`",
        "",
        "## Monitoring",
        "",
        f"- Total log entries read: `{monitoring['total_log_entries_read']}`",
        f"- Entries summarized: `{monitoring['entries_summarized']}`",
        f"- Signal counts: `{monitoring['signal_decision_counts']}`",
        f"- Response counts: `{monitoring['response_action_counts']}`",
        f"- Risk counts: `{monitoring['risk_level_counts']}`",
        f"- Stale-data count: `{monitoring['stale_data_flag_count']}`",
        f"- Top risk flags: `{monitoring['top_risk_flags']}`",
        "",
        "## Paper State",
        "",
        f"- Available: `{paper_state['available']}`",
        f"- Open position: `{paper_state['open_position']}`",
        f"- Side: `{paper_state['position_side']}`",
        f"- Entry time: `{paper_state['entry_time']}`",
        f"- Entry price: `{paper_state['entry_price']}`",
        "",
        "## Warnings",
        "",
    ]
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_json_report(report: PaperStatusReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(status_json(report) + "\n", encoding="utf-8")
    return target


def write_markdown_report(report: PaperStatusReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_markdown_report(report), encoding="utf-8")
    return target
