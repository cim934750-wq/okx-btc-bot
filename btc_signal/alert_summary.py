from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btc_signal.models import to_jsonable


SEVERITIES: tuple[str, ...] = ("INFO", "WARN", "BLOCKED")
BLOCKING_RISK_FLAGS: set[str] = {
    "stale_data",
    "signal_blocked",
    "missing_feature_frame",
    "missing_feature_columns",
    "nan_latest_features",
    "missing_signal_timestamp",
    "invalid_atr",
    "drawdown_guard",
}
APPROACHING_STALE_HOURS = 6.0
LATEST_REVIEW_REPORT = "btc_daily_review_report_latest.json"
LATEST_SNAPSHOT = "btc_daily_review_latest.json"


@dataclass(slots=True)
class AlertSummary:
    generated_at: str
    mode: str
    safety: dict[str, Any]
    source: dict[str, Any]
    overall_severity: str
    primary_reason: str
    alert_items: list[dict[str, Any]]
    blocked_reasons: list[str]
    warn_reasons: list[str]
    info_items: list[str]
    changed_fields: list[str]
    new_risk_flags: list[str]
    resolved_risk_flags: list[str]
    data_freshness_summary: dict[str, Any]
    signal_summary: dict[str, Any]
    risk_response_summary: dict[str, Any]
    paper_state_summary: dict[str, Any]
    recommended_human_action: list[str]
    warnings: list[str]


def _utc_now_iso(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat()


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _str_list(value: Any) -> list[str]:
    return [str(item) for item in _safe_list(value)]


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _load_json_object(path: str | Path) -> tuple[dict[str, Any] | None, str | None]:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"JSON input could not be read: {target}: {exc}"
    if not isinstance(payload, dict):
        return None, f"JSON input was not an object: {target}"
    return payload, None


def _default_input_path(snapshot_dir: str | Path) -> tuple[Path, str]:
    directory = Path(snapshot_dir)
    review_path = directory / LATEST_REVIEW_REPORT
    if review_path.exists():
        return review_path, "review_json"
    return directory / LATEST_SNAPSHOT, "snapshot_json"


def _compare_snapshots(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    if previous is None:
        return {
            "previous_available": False,
            "summary": "No previous snapshot available for alert comparison.",
            "changed_fields": [],
            "new_risk_flags": [],
            "resolved_risk_flags": [],
            "signal_decision_changed": False,
            "long1_active_changed": False,
            "confidence_changed": False,
            "risk_level_changed": False,
            "response_action_changed": False,
            "paper_position_change": "no_previous",
            "monitoring_log_count": {
                "previous": None,
                "current": current.get("monitoring_total_entries"),
                "delta": None,
                "changed": False,
            },
            "monitoring_stale_data_count": {
                "previous": None,
                "current": current.get("monitoring_stale_data_count"),
                "delta": None,
                "changed": False,
            },
            "warning_count": {
                "previous": None,
                "current": len(_safe_list(current.get("warnings"))),
                "delta": None,
                "changed": False,
            },
        }

    changed_fields = []
    for field in (
        "latest_candle_timestamp",
        "stale_status",
        "signal_decision",
        "long1_active",
        "confidence",
        "risk_level",
        "response_action",
        "paper_side",
    ):
        if previous.get(field) != current.get(field):
            changed_fields.append(field)
    if previous.get("paper_position_open") != current.get("paper_position_open"):
        changed_fields.append("paper_position_open")

    previous_flags = set(_str_list(previous.get("risk_flags")))
    current_flags = set(_str_list(current.get("risk_flags")))
    new_risk_flags = sorted(current_flags - previous_flags)
    resolved_risk_flags = sorted(previous_flags - current_flags)
    if new_risk_flags or resolved_risk_flags:
        changed_fields.append("risk_flags")

    previous_total = previous.get("monitoring_total_entries")
    current_total = current.get("monitoring_total_entries")
    log_delta = current_total - previous_total if isinstance(previous_total, int) and isinstance(current_total, int) else None
    if log_delta not in (None, 0):
        changed_fields.append("monitoring_total_entries")

    previous_stale_count = previous.get("monitoring_stale_data_count")
    current_stale_count = current.get("monitoring_stale_data_count")
    stale_delta = (
        current_stale_count - previous_stale_count
        if isinstance(previous_stale_count, int) and isinstance(current_stale_count, int)
        else None
    )
    if stale_delta not in (None, 0):
        changed_fields.append("monitoring_stale_data_count")

    previous_warning_count = len(_safe_list(previous.get("warnings")))
    current_warning_count = len(_safe_list(current.get("warnings")))
    warning_delta = current_warning_count - previous_warning_count
    if warning_delta:
        changed_fields.append("warning_count")

    return {
        "previous_available": True,
        "summary": "Changes detected." if changed_fields else "No compared fields changed.",
        "changed_fields": sorted(set(changed_fields)),
        "new_risk_flags": new_risk_flags,
        "resolved_risk_flags": resolved_risk_flags,
        "signal_decision_changed": previous.get("signal_decision") != current.get("signal_decision"),
        "long1_active_changed": previous.get("long1_active") != current.get("long1_active"),
        "confidence_changed": previous.get("confidence") != current.get("confidence"),
        "risk_level_changed": previous.get("risk_level") != current.get("risk_level"),
        "response_action_changed": previous.get("response_action") != current.get("response_action"),
        "paper_position_change": _paper_position_change(
            previous.get("paper_position_open"),
            current.get("paper_position_open"),
        ),
        "monitoring_log_count": {
            "previous": previous_total,
            "current": current_total,
            "delta": log_delta,
            "changed": log_delta not in (None, 0),
        },
        "monitoring_stale_data_count": {
            "previous": previous_stale_count,
            "current": current_stale_count,
            "delta": stale_delta,
            "changed": stale_delta not in (None, 0),
        },
        "warning_count": {
            "previous": previous_warning_count,
            "current": current_warning_count,
            "delta": warning_delta,
            "changed": warning_delta != 0,
        },
    }


def _paper_position_change(previous_open: Any, current_open: Any) -> str:
    if previous_open is False and current_open is True:
        return "opened"
    if previous_open is True and current_open is False:
        return "closed"
    if previous_open == current_open:
        return "unchanged"
    return "changed_unknown"


def _extract_snapshot_and_comparison(
    payload: dict[str, Any],
    *,
    compare_to: str | Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    warnings: list[str] = []
    if isinstance(payload.get("snapshot"), dict):
        snapshot = payload["snapshot"]
        comparison = payload.get("comparison") if isinstance(payload.get("comparison"), dict) else None
    else:
        snapshot = payload
        comparison = None

    if not _looks_like_snapshot(snapshot):
        return None, _compare_snapshots({}, None), ["Input did not contain a valid daily review snapshot."]

    if compare_to is not None:
        previous, error = _load_json_object(compare_to)
        if error:
            warnings.append(error)
            comparison = _compare_snapshots(snapshot, None)
        else:
            previous_snapshot = previous.get("snapshot") if isinstance(previous.get("snapshot"), dict) else previous
            comparison = _compare_snapshots(snapshot, previous_snapshot if _looks_like_snapshot(previous_snapshot) else None)
            if not _looks_like_snapshot(previous_snapshot):
                warnings.append(f"Comparison input did not contain a valid snapshot: {compare_to}")
    elif comparison is None:
        comparison = _compare_snapshots(snapshot, None)

    return snapshot, comparison, warnings


def _looks_like_snapshot(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "review_timestamp_utc",
        "latest_candle_timestamp",
        "stale_status",
        "signal_decision",
        "risk_level",
        "response_action",
        "risk_flags",
        "paper_position_open",
    }
    return required.issubset(set(value))


def load_alert_input(
    *,
    review_json: str | Path | None = None,
    snapshot_json: str | Path | None = None,
    snapshot_dir: str | Path = "runtime/daily_reviews",
    compare_to: str | Path | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    if review_json is not None and snapshot_json is not None:
        return None, _compare_snapshots({}, None), {}, ["Use either --review-json or --snapshot-json, not both."]

    if review_json is not None:
        input_path = Path(review_json)
        input_kind = "review_json"
    elif snapshot_json is not None:
        input_path = Path(snapshot_json)
        input_kind = "snapshot_json"
    else:
        input_path, input_kind = _default_input_path(snapshot_dir)

    source = {
        "input_kind": input_kind,
        "input_path": str(input_path),
        "snapshot_dir": str(snapshot_dir),
        "compare_to": str(compare_to) if compare_to is not None else None,
    }
    payload, error = _load_json_object(input_path)
    if error:
        warnings.append(error)
        return None, _compare_snapshots({}, None), source, warnings

    snapshot, comparison, extract_warnings = _extract_snapshot_and_comparison(payload, compare_to=compare_to)
    warnings.extend(extract_warnings)
    return snapshot, comparison, source, warnings


def build_alert_summary(
    *,
    review_json: str | Path | None = None,
    snapshot_json: str | Path | None = None,
    snapshot_dir: str | Path = "runtime/daily_reviews",
    compare_to: str | Path | None = None,
    now: datetime | None = None,
) -> AlertSummary:
    snapshot, comparison, source, load_warnings = load_alert_input(
        review_json=review_json,
        snapshot_json=snapshot_json,
        snapshot_dir=snapshot_dir,
        compare_to=compare_to,
    )
    blocked_reasons: list[str] = []
    warn_reasons: list[str] = []
    info_items: list[str] = []
    alert_items: list[dict[str, Any]] = []

    if snapshot is None:
        blocked_reasons.append("Daily review snapshot/report is missing or malformed.")
        for warning in load_warnings:
            blocked_reasons.append(warning)
        snapshot = _empty_snapshot()
        comparison = _compare_snapshots(snapshot, None)
    else:
        _classify_snapshot(snapshot, comparison, blocked_reasons, warn_reasons, info_items)

    for reason in blocked_reasons:
        alert_items.append({"severity": "BLOCKED", "reason": reason})
    for reason in warn_reasons:
        alert_items.append({"severity": "WARN", "reason": reason})
    for item in info_items:
        alert_items.append({"severity": "INFO", "reason": item})

    if blocked_reasons:
        severity = "BLOCKED"
        primary_reason = blocked_reasons[0]
    elif warn_reasons:
        severity = "WARN"
        primary_reason = warn_reasons[0]
    else:
        severity = "INFO"
        primary_reason = "Paper dry-run status is informational; no blocking or warning alert rules fired."

    return AlertSummary(
        generated_at=_utc_now_iso(now),
        mode="paper_daily_alert_summary_read_only",
        safety={
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
            "external_notifications_enabled": False,
            "read_only_alert_summary": True,
            "refreshes_data_by_default": False,
        },
        source=source,
        overall_severity=severity,
        primary_reason=primary_reason,
        alert_items=alert_items,
        blocked_reasons=_dedupe(blocked_reasons),
        warn_reasons=_dedupe(warn_reasons),
        info_items=_dedupe(info_items),
        changed_fields=_str_list(comparison.get("changed_fields")),
        new_risk_flags=_str_list(comparison.get("new_risk_flags")),
        resolved_risk_flags=_str_list(comparison.get("resolved_risk_flags")),
        data_freshness_summary=_data_freshness_summary(snapshot),
        signal_summary=_signal_summary(snapshot),
        risk_response_summary=_risk_response_summary(snapshot),
        paper_state_summary=_paper_state_summary(snapshot),
        recommended_human_action=_recommended_actions(severity),
        warnings=_dedupe([*load_warnings, *_str_list(snapshot.get("warnings"))]),
    )


def _empty_snapshot() -> dict[str, Any]:
    return {
        "review_timestamp_utc": None,
        "data_path": None,
        "row_count": None,
        "latest_candle_timestamp": None,
        "latest_candle_age_hours": None,
        "stale_status": "unknown",
        "signal_decision": "UNKNOWN",
        "long1_active": False,
        "confidence": "none",
        "passed_condition_count": 0,
        "missing_condition_count": 0,
        "main_missing_conditions": [],
        "risk_level": "BLOCK",
        "risk_flags": ["snapshot_unavailable"],
        "response_action": "BLOCK",
        "paper_position_open": None,
        "paper_side": None,
        "paper_entry_time": None,
        "paper_entry_price": None,
        "monitoring_total_entries": None,
        "monitoring_entries_summarized": None,
        "monitoring_signal_counts": {},
        "monitoring_response_counts": {},
        "monitoring_risk_counts": {},
        "monitoring_stale_data_count": None,
        "monitoring_top_risk_flags": [],
        "warnings": [],
    }


def _classify_snapshot(
    snapshot: dict[str, Any],
    comparison: dict[str, Any],
    blocked_reasons: list[str],
    warn_reasons: list[str],
    info_items: list[str],
) -> None:
    risk_flags = set(_str_list(snapshot.get("risk_flags")))
    warnings = _str_list(snapshot.get("warnings"))
    new_risk_flags = set(_str_list(comparison.get("new_risk_flags")))

    if "stale_data" in risk_flags:
        blocked_reasons.append("stale_data risk flag is active.")
    if snapshot.get("response_action") == "BLOCK":
        blocked_reasons.append("Latest response action is BLOCK.")
    if snapshot.get("risk_level") == "BLOCK":
        blocked_reasons.append("Latest risk level is BLOCK.")
    if _required_inputs_missing(snapshot, warnings):
        blocked_reasons.append("Required data/log/state appears missing in the review snapshot.")
    if _paper_state_inconsistent(snapshot):
        blocked_reasons.append("Paper state is internally inconsistent.")
    if BLOCKING_RISK_FLAGS.intersection(new_risk_flags):
        blocked_reasons.append(
            "New blocking risk flag(s) appeared: " + ", ".join(sorted(BLOCKING_RISK_FLAGS.intersection(new_risk_flags))) + "."
        )

    if comparison.get("signal_decision_changed"):
        warn_reasons.append("Signal decision changed since the prior snapshot.")
    if comparison.get("confidence_changed"):
        warn_reasons.append("Signal confidence changed since the prior snapshot.")
    if snapshot.get("long1_active") is True and snapshot.get("response_action") != "PAPER_LONG":
        warn_reasons.append("Long1 is active, but response is not PAPER_LONG.")
    nonblocking_new_flags = sorted(new_risk_flags - BLOCKING_RISK_FLAGS)
    if nonblocking_new_flags:
        warn_reasons.append("New non-blocking risk flag(s) appeared: " + ", ".join(nonblocking_new_flags) + ".")
    if _approaching_stale(snapshot):
        warn_reasons.append("Latest candle age is approaching the stale-data threshold.")
    if _monitoring_stopped(comparison):
        warn_reasons.append("Monitoring log count did not increase versus the prior snapshot.")
    warning_delta = comparison.get("warning_count", {}).get("delta")
    if isinstance(warning_delta, int) and warning_delta > 0:
        warn_reasons.append("Warning count increased since the prior snapshot.")

    if snapshot.get("stale_status") == "fresh":
        info_items.append("Data freshness status is fresh.")
    if snapshot.get("signal_decision") in {"WAIT", "WATCH"} and snapshot.get("risk_level") != "BLOCK":
        info_items.append("Signal remains WAIT/WATCH with no blocking risk level.")
    if snapshot.get("paper_position_open") is False and comparison.get("paper_position_change") in {"unchanged", "no_previous"}:
        info_items.append("Paper state is closed and unchanged.")
    if not new_risk_flags:
        info_items.append("No new risk flags appeared.")


def _required_inputs_missing(snapshot: dict[str, Any], warnings: list[str]) -> bool:
    if snapshot.get("row_count") in (None, 0):
        return True
    if snapshot.get("monitoring_total_entries") in (None, 0):
        return True
    if snapshot.get("paper_position_open") is None:
        return True
    lowered = " ".join(warnings).lower()
    return any(token in lowered for token in ("missing decision log", "paper state file is missing", "csv is missing"))


def _paper_state_inconsistent(snapshot: dict[str, Any]) -> bool:
    open_position = snapshot.get("paper_position_open")
    side = snapshot.get("paper_side")
    entry_time = snapshot.get("paper_entry_time")
    entry_price = snapshot.get("paper_entry_price")
    if open_position is True:
        return not side or entry_time is None or entry_price is None
    if open_position is False:
        return side is not None or entry_time is not None or entry_price is not None
    return True


def _approaching_stale(snapshot: dict[str, Any]) -> bool:
    age = snapshot.get("latest_candle_age_hours")
    return (
        isinstance(age, (int, float))
        and age >= APPROACHING_STALE_HOURS
        and snapshot.get("stale_status") != "stale"
        and "stale_data" not in set(_str_list(snapshot.get("risk_flags")))
    )


def _monitoring_stopped(comparison: dict[str, Any]) -> bool:
    if not comparison.get("previous_available"):
        return False
    delta = comparison.get("monitoring_log_count", {}).get("delta")
    return delta == 0


def _data_freshness_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "data_path": snapshot.get("data_path"),
        "row_count": snapshot.get("row_count"),
        "latest_candle_timestamp": snapshot.get("latest_candle_timestamp"),
        "latest_candle_age_hours": snapshot.get("latest_candle_age_hours"),
        "stale_status": snapshot.get("stale_status"),
    }


def _signal_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "signal_decision": snapshot.get("signal_decision"),
        "long1_active": snapshot.get("long1_active"),
        "confidence": snapshot.get("confidence"),
        "passed_condition_count": snapshot.get("passed_condition_count"),
        "missing_condition_count": snapshot.get("missing_condition_count"),
        "main_missing_conditions": snapshot.get("main_missing_conditions"),
    }


def _risk_response_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_level": snapshot.get("risk_level"),
        "risk_flags": snapshot.get("risk_flags"),
        "response_action": snapshot.get("response_action"),
    }


def _paper_state_summary(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_position_open": snapshot.get("paper_position_open"),
        "paper_side": snapshot.get("paper_side"),
        "paper_entry_time": snapshot.get("paper_entry_time"),
        "paper_entry_price": snapshot.get("paper_entry_price"),
    }


def _recommended_actions(severity: str) -> list[str]:
    if severity == "BLOCKED":
        return [
            "Refresh public BTC data manually if stale.",
            "Rerun the paper signal once after data refresh.",
            "Rerun the daily dry-run review.",
            "Inspect active risk flags before any further paper action.",
            "Keep paper mode only; do not trade.",
        ]
    if severity == "WARN":
        return [
            "Inspect changed fields and new risk flags.",
            "Rerun the daily review after the next paper signal/log update.",
            "Keep paper mode only; do not trade.",
        ]
    return [
        "Continue paper-mode observation.",
        "Review the next daily snapshot before changing any automation.",
        "Keep paper mode only; do not trade.",
    ]


def summary_to_dict(summary: AlertSummary) -> dict[str, Any]:
    return to_jsonable(asdict(summary))


def summary_json(summary: AlertSummary) -> str:
    return json.dumps(summary_to_dict(summary), indent=2, sort_keys=True)


def format_text_summary(summary: AlertSummary) -> str:
    payload = summary_to_dict(summary)
    lines = [
        "BTC Daily Alert Summary",
        f"generated_at: {payload['generated_at']}",
        f"mode: {payload['mode']}",
        f"overall_severity: {payload['overall_severity']}",
        f"primary_reason: {payload['primary_reason']}",
        f"blocked_reasons: {payload['blocked_reasons']}",
        f"warn_reasons: {payload['warn_reasons']}",
        f"info_items: {payload['info_items']}",
        f"changed_fields: {payload['changed_fields']}",
        f"new_risk_flags: {payload['new_risk_flags']}",
        f"resolved_risk_flags: {payload['resolved_risk_flags']}",
        f"data_freshness: {payload['data_freshness_summary']}",
        f"signal: {payload['signal_summary']}",
        f"risk_response: {payload['risk_response_summary']}",
        f"paper_state: {payload['paper_state_summary']}",
        f"recommended_human_action: {payload['recommended_human_action']}",
        f"warnings: {payload['warnings']}",
    ]
    return "\n".join(lines) + "\n"


def format_markdown_summary(summary: AlertSummary) -> str:
    payload = summary_to_dict(summary)
    lines = [
        "# BTC Daily Alert Summary",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Overall severity: `{payload['overall_severity']}`",
        f"- Primary reason: `{payload['primary_reason']}`",
        f"- External notifications enabled: `{payload['safety']['external_notifications_enabled']}`",
        f"- Live orders enabled: `{payload['safety']['live_orders_enabled']}`",
        "",
        "## Reasons",
        "",
        f"- Blocked: `{payload['blocked_reasons']}`",
        f"- Warn: `{payload['warn_reasons']}`",
        f"- Info: `{payload['info_items']}`",
        "",
        "## Changes",
        "",
        f"- Changed fields: `{payload['changed_fields']}`",
        f"- New risk flags: `{payload['new_risk_flags']}`",
        f"- Resolved risk flags: `{payload['resolved_risk_flags']}`",
        "",
        "## Current State",
        "",
        f"- Data freshness: `{payload['data_freshness_summary']}`",
        f"- Signal: `{payload['signal_summary']}`",
        f"- Risk/response: `{payload['risk_response_summary']}`",
        f"- Paper state: `{payload['paper_state_summary']}`",
        "",
        "## Recommended Human Action",
        "",
    ]
    lines.extend(f"- {action}" for action in payload["recommended_human_action"])
    lines.extend(["", "## Warnings", ""])
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_summary_json(summary: AlertSummary, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(summary_json(summary) + "\n", encoding="utf-8")
    return target


def write_summary_markdown(summary: AlertSummary, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_markdown_summary(summary), encoding="utf-8")
    return target
