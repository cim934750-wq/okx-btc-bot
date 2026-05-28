from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btc_signal.models import to_jsonable


SIGNAL_DECISIONS: tuple[str, ...] = ("WAIT", "WATCH", "LONG_SIGNAL", "BLOCKED")
RESPONSE_ACTIONS: tuple[str, ...] = ("WAIT", "WATCH", "PAPER_LONG", "BLOCK", "EXIT_WARNING")
RISK_LEVELS: tuple[str, ...] = ("LOW", "MEDIUM", "HIGH", "BLOCK")
PAPER_STATE_FIELDS: tuple[str, ...] = (
    "open_position",
    "position_side",
    "entry_time",
    "entry_price",
    "last_signal_time",
    "paper_equity",
    "max_drawdown_seen",
)


@dataclass(slots=True)
class LogReadResult:
    entries: list[dict[str, Any]]
    files_read: list[str] = field(default_factory=list)
    missing_paths: list[str] = field(default_factory=list)
    malformed_line_count: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MonitoringReport:
    generated_at: str
    mode: str
    safety: dict[str, Any]
    log_source: dict[str, Any]
    metrics: dict[str, Any]
    latest_decision: dict[str, Any] | None
    paper_state: dict[str, Any]
    paper_state_changes: list[dict[str, Any]]
    warnings: list[str]


def _utc_now_iso(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat()


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


def _nested_get(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _counter_dict(counter: Counter[str], known_keys: tuple[str, ...]) -> dict[str, int]:
    output = {key: int(counter.get(key, 0)) for key in known_keys}
    for key in sorted(counter):
        output.setdefault(key, int(counter[key]))
    return output


def _top_items(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [
        {"name": name, "count": int(count)}
        for name, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def resolve_log_files(log_path: str | Path | None = None, logs_dir: str | Path | None = None) -> tuple[list[Path], list[str]]:
    missing: list[str] = []
    if log_path is not None:
        path = Path(log_path)
        if path.exists() and path.is_file():
            return [path], missing
        missing.append(str(path))
        return [], missing

    directory = Path(logs_dir) if logs_dir is not None else Path("runtime/logs")
    if not directory.exists():
        missing.append(str(directory))
        return [], missing
    files = sorted(directory.glob("btc_signal_decisions_*.jsonl"))
    if not files:
        missing.append(str(directory / "btc_signal_decisions_*.jsonl"))
    return files, missing


def read_decision_logs(log_path: str | Path | None = None, logs_dir: str | Path | None = None) -> LogReadResult:
    files, missing = resolve_log_files(log_path=log_path, logs_dir=logs_dir)
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    malformed_count = 0

    for missing_path in missing:
        warnings.append(f"Missing decision log path: {missing_path}")

    sequence = 0
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            warnings.append(f"Could not read decision log {path}: {exc}")
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                malformed_count += 1
                warnings.append(f"Malformed JSONL line skipped: {path}:{line_number}")
                continue
            if not isinstance(payload, dict):
                malformed_count += 1
                warnings.append(f"Non-object JSONL line skipped: {path}:{line_number}")
                continue
            sequence += 1
            payload["_monitoring_source"] = {
                "path": str(path),
                "line_number": line_number,
                "sequence": sequence,
            }
            entries.append(payload)

    return LogReadResult(
        entries=entries,
        files_read=[str(path) for path in files],
        missing_paths=missing,
        malformed_line_count=malformed_count,
        warnings=warnings,
    )


def _latest_decision_summary(entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if entry is None:
        return None
    return {
        "run_at": entry.get("run_at"),
        "signal_timestamp": _nested_get(entry, "signal", "timestamp"),
        "signal_decision": _nested_get(entry, "signal", "decision"),
        "signal_name": _nested_get(entry, "signal", "signal_name"),
        "confidence_label": _nested_get(entry, "signal", "confidence_label"),
        "risk_level": _nested_get(entry, "risk", "risk_level"),
        "risk_flags": _safe_list(_nested_get(entry, "risk", "risk_flags")),
        "response_action": _nested_get(entry, "response", "action"),
        "response_reason": _nested_get(entry, "response", "reason"),
        "close": _nested_get(entry, "signal", "evidence", "close"),
        "source": entry.get("_monitoring_source"),
    }


def _summarize_paper_state(state: dict[str, Any] | None, source: str) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {
            "source": source,
            "available": False,
            "open_position": None,
            "position_side": None,
            "entry_time": None,
            "entry_price": None,
            "last_signal_time": None,
            "paper_equity": None,
            "max_drawdown_seen": None,
            "notes_count": 0,
        }
    return {
        "source": source,
        "available": True,
        "open_position": state.get("open_position"),
        "position_side": state.get("position_side"),
        "entry_time": state.get("entry_time"),
        "entry_price": state.get("entry_price"),
        "last_signal_time": state.get("last_signal_time"),
        "paper_equity": state.get("paper_equity"),
        "max_drawdown_seen": state.get("max_drawdown_seen"),
        "notes_count": len(state.get("notes", [])) if isinstance(state.get("notes"), list) else 0,
    }


def load_paper_state_summary(
    state_path: str | Path | None,
    latest_entry: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if state_path is not None:
        path = Path(state_path)
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                warnings.append(f"Could not read paper state {path}: {exc}")
            else:
                return _summarize_paper_state(payload, str(path)), warnings
        else:
            warnings.append(f"Missing paper state path: {path}")

    log_state = _nested_get(latest_entry or {}, "paper_state")
    if isinstance(log_state, dict):
        return _summarize_paper_state(log_state, "latest_decision_log"), warnings
    return _summarize_paper_state(None, "missing"), warnings


def infer_paper_state_changes(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    previous_state: dict[str, Any] | None = None
    for entry in entries:
        state = _nested_get(entry, "paper_state")
        if not isinstance(state, dict):
            continue
        if previous_state is None:
            previous_state = state
            continue
        changed_fields: dict[str, dict[str, Any]] = {}
        for field_name in PAPER_STATE_FIELDS:
            before = previous_state.get(field_name)
            after = state.get(field_name)
            if before != after:
                changed_fields[field_name] = {"before": before, "after": after}
        if changed_fields:
            changes.append(
                {
                    "run_at": entry.get("run_at"),
                    "signal_timestamp": _nested_get(entry, "signal", "timestamp"),
                    "changed_fields": changed_fields,
                    "source": entry.get("_monitoring_source"),
                }
            )
        previous_state = state
    return changes


def build_monitoring_report(
    *,
    log_path: str | Path | None = None,
    logs_dir: str | Path | None = None,
    state_path: str | Path | None = None,
    limit: int = 20,
    now: datetime | None = None,
    log_stale_after_hours: float = 24.0,
) -> MonitoringReport:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    read_result = read_decision_logs(log_path=log_path, logs_dir=logs_dir)
    valid_entries = read_result.entries
    summarized_entries = valid_entries[-limit:]
    latest_entry = summarized_entries[-1] if summarized_entries else None

    signal_counter: Counter[str] = Counter()
    response_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    risk_flag_counter: Counter[str] = Counter()
    stale_data_flag_count = 0
    long1_active_count = 0

    for entry in summarized_entries:
        signal_decision = _nested_get(entry, "signal", "decision")
        response_action = _nested_get(entry, "response", "action")
        risk_level = _nested_get(entry, "risk", "risk_level")
        if signal_decision:
            signal_counter[str(signal_decision)] += 1
        if response_action:
            response_counter[str(response_action)] += 1
        if risk_level:
            risk_counter[str(risk_level)] += 1
        risk_flags = [str(flag) for flag in _safe_list(_nested_get(entry, "risk", "risk_flags"))]
        risk_flag_counter.update(risk_flags)
        if "stale_data" in risk_flags:
            stale_data_flag_count += 1
        if _nested_get(entry, "signal", "signal_name") == "Long1":
            long1_active_count += 1

    first_run_at = summarized_entries[0].get("run_at") if summarized_entries else None
    latest_run_at = latest_entry.get("run_at") if latest_entry else None
    latest_candle_timestamp = _nested_get(latest_entry or {}, "signal", "timestamp")
    paper_state_summary, state_warnings = load_paper_state_summary(state_path, latest_entry)
    paper_state_changes = infer_paper_state_changes(summarized_entries)

    warnings = [*read_result.warnings, *state_warnings]
    if not summarized_entries:
        warnings.append("No decision log entries were available to summarize.")
    if read_result.malformed_line_count:
        warnings.append(f"Skipped {read_result.malformed_line_count} malformed decision log line(s).")
    if stale_data_flag_count:
        warnings.append(f"stale_data appeared in {stale_data_flag_count} summarized decision(s).")
    latest_run_dt = _parse_time(latest_run_at)
    if latest_run_dt is not None:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        age_hours = (current.astimezone(timezone.utc) - latest_run_dt).total_seconds() / 3600.0
        if age_hours > log_stale_after_hours:
            warnings.append(
                f"Latest decision log is {age_hours:.2f} hours old; limit is {log_stale_after_hours:.2f} hours."
            )
    elif summarized_entries:
        warnings.append("Latest decision log has no parseable run_at timestamp.")

    metrics = {
        "total_log_entries_read": len(valid_entries),
        "entries_summarized": len(summarized_entries),
        "malformed_line_count": read_result.malformed_line_count,
        "first_decision_timestamp": first_run_at,
        "latest_decision_timestamp": latest_run_at,
        "latest_candle_timestamp": latest_candle_timestamp,
        "stale_data_flag_count": stale_data_flag_count,
        "signal_decision_counts": _counter_dict(signal_counter, SIGNAL_DECISIONS),
        "response_action_counts": _counter_dict(response_counter, RESPONSE_ACTIONS),
        "risk_level_counts": _counter_dict(risk_counter, RISK_LEVELS),
        "top_risk_flags": _top_items(risk_flag_counter),
        "long1_active_count": long1_active_count,
        "paper_long_count": int(response_counter.get("PAPER_LONG", 0)),
        "block_count": int(response_counter.get("BLOCK", 0)),
        "watch_count": int(response_counter.get("WATCH", 0)),
        "exit_warning_count": int(response_counter.get("EXIT_WARNING", 0)),
        "paper_state_change_count": len(paper_state_changes),
    }

    return MonitoringReport(
        generated_at=_utc_now_iso(now),
        mode="paper_dry_run_monitoring_only",
        safety={
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
            "read_only_report": True,
        },
        log_source={
            "log_path": str(log_path) if log_path is not None else None,
            "logs_dir": str(logs_dir) if logs_dir is not None else None,
            "files_read": read_result.files_read,
            "missing_paths": read_result.missing_paths,
            "limit": limit,
        },
        metrics=metrics,
        latest_decision=_latest_decision_summary(latest_entry),
        paper_state=paper_state_summary,
        paper_state_changes=paper_state_changes,
        warnings=warnings,
    )


def report_to_dict(report: MonitoringReport) -> dict[str, Any]:
    return to_jsonable(asdict(report))


def monitoring_json(report: MonitoringReport) -> str:
    return json.dumps(report_to_dict(report), indent=2, sort_keys=True)


def format_text_report(report: MonitoringReport) -> str:
    payload = report_to_dict(report)
    metrics = payload["metrics"]
    latest = payload["latest_decision"] or {}
    paper_state = payload["paper_state"]
    lines = [
        "BTC Dry-Run Monitoring Report",
        f"generated_at: {payload['generated_at']}",
        f"mode: {payload['mode']}",
        f"total_log_entries_read: {metrics['total_log_entries_read']}",
        f"entries_summarized: {metrics['entries_summarized']}",
        f"first_decision_timestamp: {metrics['first_decision_timestamp']}",
        f"latest_decision_timestamp: {metrics['latest_decision_timestamp']}",
        f"latest_candle_timestamp: {metrics['latest_candle_timestamp']}",
        f"stale_data_flag_count: {metrics['stale_data_flag_count']}",
        f"signal_decision_counts: {metrics['signal_decision_counts']}",
        f"response_action_counts: {metrics['response_action_counts']}",
        f"risk_level_counts: {metrics['risk_level_counts']}",
        f"top_risk_flags: {metrics['top_risk_flags']}",
        f"long1_active_count: {metrics['long1_active_count']}",
        f"paper_state_change_count: {metrics['paper_state_change_count']}",
        (
            "latest_decision: "
            f"signal={latest.get('signal_decision')} risk={latest.get('risk_level')} "
            f"response={latest.get('response_action')}"
        ),
        (
            "paper_state: "
            f"open_position={paper_state.get('open_position')} "
            f"side={paper_state.get('position_side')} "
            f"entry_time={paper_state.get('entry_time')}"
        ),
        f"warnings: {payload['warnings']}",
    ]
    return "\n".join(lines) + "\n"


def format_markdown_report(report: MonitoringReport) -> str:
    payload = report_to_dict(report)
    metrics = payload["metrics"]
    latest = payload["latest_decision"] or {}
    paper_state = payload["paper_state"]
    lines = [
        "# BTC Dry-Run Monitoring Report",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Total log entries read: `{metrics['total_log_entries_read']}`",
        f"- Entries summarized: `{metrics['entries_summarized']}`",
        f"- First decision timestamp: `{metrics['first_decision_timestamp']}`",
        f"- Latest decision timestamp: `{metrics['latest_decision_timestamp']}`",
        f"- Latest candle timestamp: `{metrics['latest_candle_timestamp']}`",
        f"- Stale-data flag count: `{metrics['stale_data_flag_count']}`",
        f"- Long1 active count: `{metrics['long1_active_count']}`",
        f"- Paper state changes: `{metrics['paper_state_change_count']}`",
        "",
        "## Counts",
        "",
        f"- Signal decisions: `{metrics['signal_decision_counts']}`",
        f"- Response actions: `{metrics['response_action_counts']}`",
        f"- Risk levels: `{metrics['risk_level_counts']}`",
        f"- Top risk flags: `{metrics['top_risk_flags']}`",
        "",
        "## Latest Decision",
        "",
        f"- Signal: `{latest.get('signal_decision')}`",
        f"- Signal name: `{latest.get('signal_name')}`",
        f"- Confidence: `{latest.get('confidence_label')}`",
        f"- Risk: `{latest.get('risk_level')}`",
        f"- Response: `{latest.get('response_action')}`",
        "",
        "## Paper State",
        "",
        f"- Available: `{paper_state.get('available')}`",
        f"- Open position: `{paper_state.get('open_position')}`",
        f"- Position side: `{paper_state.get('position_side')}`",
        f"- Entry time: `{paper_state.get('entry_time')}`",
        f"- Entry price: `{paper_state.get('entry_price')}`",
        "",
        "## Warnings",
        "",
    ]
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_json_report(report: MonitoringReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(monitoring_json(report) + "\n", encoding="utf-8")
    return target


def write_markdown_report(report: MonitoringReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_markdown_report(report), encoding="utf-8")
    return target
