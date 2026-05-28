from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btc_signal.config import BtcSignalConfig
from btc_signal.models import to_jsonable
from btc_signal.status_dashboard import (
    PaperStatusReport,
    build_paper_status_report,
    report_to_dict as status_to_dict,
)


SNAPSHOT_PREFIX = "btc_daily_review"
LATEST_JSON = f"{SNAPSHOT_PREFIX}_latest.json"


@dataclass(slots=True)
class DailyReviewResult:
    generated_at: str
    mode: str
    safety: dict[str, Any]
    snapshot: dict[str, Any]
    comparison: dict[str, Any]
    output_paths: dict[str, str | None]
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


def _snapshot_stamp(value: str | None, now: datetime | None = None) -> str:
    parsed = _parse_time(value)
    if parsed is None:
        parsed = _utc_now(now)
    return parsed.strftime("%Y%m%dT%H%M%SZ")


def _sorted_unique(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values})


def snapshot_from_status_report(status_report: PaperStatusReport) -> dict[str, Any]:
    status = status_to_dict(status_report)
    data = status["data"]
    signal = status["latest_signal"]
    risk = status["latest_risk"]
    response = status["latest_response"]
    monitoring = status["monitoring"]
    paper_state = status["paper_state"]

    return {
        "review_timestamp_utc": status["generated_at"],
        "data_path": data["csv_path"],
        "row_count": data["row_count"],
        "latest_candle_timestamp": data["latest_candle_timestamp"],
        "latest_candle_age_hours": data["latest_candle_age_hours"],
        "stale_status": data["status"],
        "signal_decision": signal["decision"],
        "long1_active": signal["long1_active"],
        "confidence": signal["confidence_label"],
        "passed_condition_count": signal["passed_condition_count"],
        "missing_condition_count": signal["missing_condition_count"],
        "main_missing_conditions": signal["main_missing_conditions"],
        "risk_level": risk["risk_level"],
        "risk_flags": risk["risk_flags"],
        "response_action": response["action"],
        "paper_position_open": paper_state["open_position"],
        "paper_side": paper_state["position_side"],
        "paper_entry_time": paper_state["entry_time"],
        "paper_entry_price": paper_state["entry_price"],
        "monitoring_total_entries": monitoring["total_log_entries_read"],
        "monitoring_entries_summarized": monitoring["entries_summarized"],
        "monitoring_signal_counts": monitoring["signal_decision_counts"],
        "monitoring_response_counts": monitoring["response_action_counts"],
        "monitoring_risk_counts": monitoring["risk_level_counts"],
        "monitoring_stale_data_count": monitoring["stale_data_flag_count"],
        "monitoring_top_risk_flags": monitoring["top_risk_flags"],
        "warnings": status["warnings"],
    }


def latest_snapshot_path(snapshot_dir: str | Path) -> Path:
    return Path(snapshot_dir) / LATEST_JSON


def timestamped_snapshot_path(snapshot_dir: str | Path, snapshot: dict[str, Any]) -> Path:
    stamp = _snapshot_stamp(str(snapshot.get("review_timestamp_utc")))
    return Path(snapshot_dir) / f"{SNAPSHOT_PREFIX}_{stamp}.json"


def load_previous_snapshot(path: str | Path | None) -> tuple[dict[str, Any] | None, list[str]]:
    if path is None:
        return None, []
    target = Path(path)
    if not target.exists():
        return None, [f"Previous snapshot not found: {target}"]
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"Previous snapshot could not be read: {target}: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"Previous snapshot was not a JSON object: {target}"]
    return payload, []


def _scalar_change(previous: dict[str, Any], current: dict[str, Any], field: str) -> dict[str, Any]:
    before = previous.get(field)
    after = current.get(field)
    return {"previous": before, "current": after, "changed": before != after}


def _delta(previous: dict[str, Any], current: dict[str, Any], field: str) -> dict[str, Any]:
    before = previous.get(field)
    after = current.get(field)
    numeric_delta = None
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        numeric_delta = after - before
    return {"previous": before, "current": after, "delta": numeric_delta, "changed": before != after}


def _paper_position_change(previous_open: Any, current_open: Any) -> str:
    if previous_open is False and current_open is True:
        return "opened"
    if previous_open is True and current_open is False:
        return "closed"
    if previous_open == current_open:
        return "unchanged"
    return "changed_unknown"


def compare_snapshots(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    previous_path: str | Path | None = None,
    load_warnings: list[str] | None = None,
) -> dict[str, Any]:
    warnings = list(load_warnings or [])
    if previous is None:
        return {
            "previous_available": False,
            "previous_path": str(previous_path) if previous_path is not None else None,
            "summary": "No previous snapshot available for comparison.",
            "changed_fields": [],
            "latest_candle_timestamp": {"previous": None, "current": current.get("latest_candle_timestamp"), "changed": False},
            "stale_status_changed": False,
            "signal_decision_changed": False,
            "long1_active_changed": False,
            "confidence_changed": False,
            "passed_condition_count": {"previous": None, "current": current.get("passed_condition_count"), "delta": None, "changed": False},
            "missing_condition_count": {"previous": None, "current": current.get("missing_condition_count"), "delta": None, "changed": False},
            "new_missing_conditions": [],
            "resolved_missing_conditions": [],
            "risk_level_changed": False,
            "new_risk_flags": [],
            "resolved_risk_flags": [],
            "response_action_changed": False,
            "paper_position_change": "no_previous",
            "paper_side_changed": False,
            "monitoring_log_count": {"previous": None, "current": current.get("monitoring_total_entries"), "delta": None, "changed": False},
            "monitoring_stale_data_count": {"previous": None, "current": current.get("monitoring_stale_data_count"), "delta": None, "changed": False},
            "warning_count": {"previous": None, "current": len(current.get("warnings", [])), "delta": None, "changed": False},
            "warnings": warnings,
        }

    scalar_fields = (
        "latest_candle_timestamp",
        "stale_status",
        "signal_decision",
        "long1_active",
        "confidence",
        "risk_level",
        "response_action",
        "paper_side",
    )
    changed_fields = [field for field in scalar_fields if previous.get(field) != current.get(field)]
    passed_change = _delta(previous, current, "passed_condition_count")
    missing_change = _delta(previous, current, "missing_condition_count")
    monitoring_count_change = _delta(previous, current, "monitoring_total_entries")
    stale_data_count_change = _delta(previous, current, "monitoring_stale_data_count")
    warning_count_change = {
        "previous": len(previous.get("warnings", [])) if isinstance(previous.get("warnings"), list) else 0,
        "current": len(current.get("warnings", [])) if isinstance(current.get("warnings"), list) else 0,
    }
    warning_count_change["delta"] = warning_count_change["current"] - warning_count_change["previous"]
    warning_count_change["changed"] = warning_count_change["delta"] != 0

    for field_name, change in (
        ("passed_condition_count", passed_change),
        ("missing_condition_count", missing_change),
        ("monitoring_total_entries", monitoring_count_change),
        ("monitoring_stale_data_count", stale_data_count_change),
        ("warning_count", warning_count_change),
    ):
        if change["changed"]:
            changed_fields.append(field_name)

    previous_missing = set(_sorted_unique(previous.get("main_missing_conditions")))
    current_missing = set(_sorted_unique(current.get("main_missing_conditions")))
    previous_risk_flags = set(_sorted_unique(previous.get("risk_flags")))
    current_risk_flags = set(_sorted_unique(current.get("risk_flags")))
    if previous_missing != current_missing:
        changed_fields.append("main_missing_conditions")
    if previous_risk_flags != current_risk_flags:
        changed_fields.append("risk_flags")
    if previous.get("paper_position_open") != current.get("paper_position_open"):
        changed_fields.append("paper_position_open")

    return {
        "previous_available": True,
        "previous_path": str(previous_path) if previous_path is not None else None,
        "previous_review_timestamp_utc": previous.get("review_timestamp_utc"),
        "current_review_timestamp_utc": current.get("review_timestamp_utc"),
        "summary": "Changes detected." if changed_fields else "No compared fields changed.",
        "changed_fields": sorted(set(changed_fields)),
        "latest_candle_timestamp": _scalar_change(previous, current, "latest_candle_timestamp"),
        "stale_status_changed": previous.get("stale_status") != current.get("stale_status"),
        "signal_decision_changed": previous.get("signal_decision") != current.get("signal_decision"),
        "long1_active_changed": previous.get("long1_active") != current.get("long1_active"),
        "confidence_changed": previous.get("confidence") != current.get("confidence"),
        "passed_condition_count": passed_change,
        "missing_condition_count": missing_change,
        "new_missing_conditions": sorted(current_missing - previous_missing),
        "resolved_missing_conditions": sorted(previous_missing - current_missing),
        "risk_level_changed": previous.get("risk_level") != current.get("risk_level"),
        "new_risk_flags": sorted(current_risk_flags - previous_risk_flags),
        "resolved_risk_flags": sorted(previous_risk_flags - current_risk_flags),
        "response_action_changed": previous.get("response_action") != current.get("response_action"),
        "paper_position_change": _paper_position_change(
            previous.get("paper_position_open"),
            current.get("paper_position_open"),
        ),
        "paper_side_changed": previous.get("paper_side") != current.get("paper_side"),
        "monitoring_log_count": monitoring_count_change,
        "monitoring_stale_data_count": stale_data_count_change,
        "warning_count": warning_count_change,
        "warnings": warnings,
    }


def build_daily_review(
    *,
    config: BtcSignalConfig,
    snapshot_dir: str | Path,
    log_path: str | Path | None = None,
    logs_dir: str | Path | None = None,
    state_path: str | Path | None = None,
    limit: int = 20,
    compare_to: str | Path | None = None,
    now: datetime | None = None,
) -> DailyReviewResult:
    status_report = build_paper_status_report(
        config=config,
        log_path=log_path,
        logs_dir=logs_dir,
        state_path=state_path,
        limit=limit,
        now=now,
    )
    snapshot = snapshot_from_status_report(status_report)
    snapshot_target_dir = Path(snapshot_dir)
    default_previous_path = latest_snapshot_path(snapshot_target_dir)
    previous_path = Path(compare_to) if compare_to is not None else default_previous_path
    previous_snapshot, previous_warnings = load_previous_snapshot(previous_path)
    if compare_to is None and previous_path == latest_snapshot_path(snapshot_target_dir) and not previous_path.exists():
        previous_warnings = []
    comparison = compare_snapshots(
        snapshot,
        previous_snapshot,
        previous_path=previous_path,
        load_warnings=previous_warnings,
    )
    timestamped_path = timestamped_snapshot_path(snapshot_target_dir, snapshot)
    latest_path = latest_snapshot_path(snapshot_target_dir)
    write_snapshot(snapshot, timestamped_path)
    write_snapshot(snapshot, latest_path)

    warnings = list(dict.fromkeys([*snapshot.get("warnings", []), *comparison.get("warnings", [])]))
    return DailyReviewResult(
        generated_at=snapshot["review_timestamp_utc"],
        mode="paper_daily_review_read_only",
        safety={
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
            "read_only_review": True,
            "refreshes_data_by_default": False,
        },
        snapshot=snapshot,
        comparison=comparison,
        output_paths={
            "snapshot_timestamped_json": str(timestamped_path),
            "snapshot_latest_json": str(latest_path),
            "review_json": None,
            "review_markdown": None,
        },
        warnings=warnings,
    )


def review_to_dict(review: DailyReviewResult) -> dict[str, Any]:
    return to_jsonable(asdict(review))


def review_json(review: DailyReviewResult) -> str:
    return json.dumps(review_to_dict(review), indent=2, sort_keys=True)


def write_snapshot(snapshot: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(to_jsonable(snapshot), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def write_review_json(review: DailyReviewResult, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    review.output_paths["review_json"] = str(target)
    target.write_text(review_json(review) + "\n", encoding="utf-8")
    return target


def format_text_review(review: DailyReviewResult) -> str:
    payload = review_to_dict(review)
    snapshot = payload["snapshot"]
    comparison = payload["comparison"]
    lines = [
        "BTC Daily Dry-Run Review",
        f"generated_at: {payload['generated_at']}",
        f"mode: {payload['mode']}",
        f"snapshot_latest_json: {payload['output_paths']['snapshot_latest_json']}",
        f"snapshot_timestamped_json: {payload['output_paths']['snapshot_timestamped_json']}",
        f"previous_available: {comparison['previous_available']}",
        f"comparison_summary: {comparison['summary']}",
        f"changed_fields: {comparison['changed_fields']}",
        f"latest_candle_timestamp: {snapshot['latest_candle_timestamp']}",
        f"stale_status: {snapshot['stale_status']}",
        f"signal: decision={snapshot['signal_decision']} long1_active={snapshot['long1_active']} confidence={snapshot['confidence']}",
        f"conditions: passed={snapshot['passed_condition_count']} missing={snapshot['missing_condition_count']} main_missing={snapshot['main_missing_conditions']}",
        f"risk: level={snapshot['risk_level']} flags={snapshot['risk_flags']}",
        f"response_action: {snapshot['response_action']}",
        f"paper_state: open={snapshot['paper_position_open']} side={snapshot['paper_side']} entry_time={snapshot['paper_entry_time']} entry_price={snapshot['paper_entry_price']}",
        f"monitoring: total={snapshot['monitoring_total_entries']} summarized={snapshot['monitoring_entries_summarized']} stale_data_count={snapshot['monitoring_stale_data_count']}",
        f"new_missing_conditions: {comparison['new_missing_conditions']}",
        f"resolved_missing_conditions: {comparison['resolved_missing_conditions']}",
        f"new_risk_flags: {comparison['new_risk_flags']}",
        f"resolved_risk_flags: {comparison['resolved_risk_flags']}",
        f"paper_position_change: {comparison['paper_position_change']}",
        f"warnings: {payload['warnings']}",
    ]
    return "\n".join(lines) + "\n"


def format_markdown_review(review: DailyReviewResult) -> str:
    payload = review_to_dict(review)
    snapshot = payload["snapshot"]
    comparison = payload["comparison"]
    lines = [
        "# BTC Daily Dry-Run Review",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Read-only: `{payload['safety']['read_only_review']}`",
        f"- Live orders enabled: `{payload['safety']['live_orders_enabled']}`",
        f"- Snapshot latest JSON: `{payload['output_paths']['snapshot_latest_json']}`",
        f"- Snapshot timestamped JSON: `{payload['output_paths']['snapshot_timestamped_json']}`",
        "",
        "## Current Snapshot",
        "",
        f"- Latest candle: `{snapshot['latest_candle_timestamp']}`",
        f"- Candle age hours: `{snapshot['latest_candle_age_hours']}`",
        f"- Stale status: `{snapshot['stale_status']}`",
        f"- Signal: `{snapshot['signal_decision']}`",
        f"- Long1 active: `{snapshot['long1_active']}`",
        f"- Confidence: `{snapshot['confidence']}`",
        f"- Passed/missing conditions: `{snapshot['passed_condition_count']}/{snapshot['missing_condition_count']}`",
        f"- Main missing conditions: `{snapshot['main_missing_conditions']}`",
        f"- Risk level: `{snapshot['risk_level']}`",
        f"- Risk flags: `{snapshot['risk_flags']}`",
        f"- Response action: `{snapshot['response_action']}`",
        f"- Paper open: `{snapshot['paper_position_open']}`",
        f"- Paper side: `{snapshot['paper_side']}`",
        "",
        "## Comparison",
        "",
        f"- Previous available: `{comparison['previous_available']}`",
        f"- Summary: `{comparison['summary']}`",
        f"- Changed fields: `{comparison['changed_fields']}`",
        f"- New missing conditions: `{comparison['new_missing_conditions']}`",
        f"- Resolved missing conditions: `{comparison['resolved_missing_conditions']}`",
        f"- New risk flags: `{comparison['new_risk_flags']}`",
        f"- Resolved risk flags: `{comparison['resolved_risk_flags']}`",
        f"- Paper position change: `{comparison['paper_position_change']}`",
        f"- Monitoring log count delta: `{comparison['monitoring_log_count']['delta']}`",
        f"- Stale-data count delta: `{comparison['monitoring_stale_data_count']['delta']}`",
        f"- Warning count delta: `{comparison['warning_count']['delta']}`",
        "",
        "## Warnings",
        "",
    ]
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_review_markdown(review: DailyReviewResult, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    review.output_paths["review_markdown"] = str(target)
    target.write_text(format_markdown_review(review), encoding="utf-8")
    return target
