from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btc_signal.alert_summary import build_alert_summary, summary_to_dict
from btc_signal.models import to_jsonable


LATEST_ALERT_JSON = "btc_daily_alert_summary_latest.json"
COMMANDS: dict[str, str] = {
    "refresh_data": "python scripts/refresh_btcusdt_4h_data.py",
    "run_signal_once": "python scripts/run_btc_signal_once.py",
    "paper_status": "python scripts/report_btc_paper_status.py",
    "daily_review": "python scripts/review_btc_daily_dry_run.py",
    "alert_summary": "python scripts/summarize_btc_daily_alerts.py",
    "operator_checklist": "python scripts/print_btc_operator_checklist.py",
}
SAFETY_BOUNDARIES: tuple[str, ...] = (
    "Paper mode only.",
    "No API keys are required.",
    "No exchange orders are enabled.",
    "No live trading readiness is claimed.",
    "Do not override BLOCK, WARN, or risk flags manually.",
)


@dataclass(slots=True)
class OperatorChecklist:
    generated_at: str
    mode: str
    safety: dict[str, Any]
    source: dict[str, Any]
    severity: str
    primary_reason: str
    checklist_items: list[dict[str, Any]]
    exact_commands: list[str]
    safety_boundaries: list[str]
    alert_summary: dict[str, Any]
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
        return None, f"Alert input could not be read: {target}: {exc}"
    if not isinstance(payload, dict):
        return None, f"Alert input was not a JSON object: {target}"
    return payload, None


def _default_alert_path(snapshot_dir: str | Path) -> Path:
    return Path(snapshot_dir) / LATEST_ALERT_JSON


def load_or_build_alert_summary(
    *,
    alert_json: str | Path | None = None,
    review_json: str | Path | None = None,
    snapshot_dir: str | Path = "runtime/daily_reviews",
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    if alert_json is not None:
        payload, error = _load_json_object(alert_json)
        source = {
            "input_kind": "alert_json",
            "input_path": str(alert_json),
            "snapshot_dir": str(snapshot_dir),
            "built_alert_summary": False,
        }
        if error:
            warnings.append(error)
            return _malformed_alert(error), source, warnings
        if not _looks_like_alert(payload):
            warning = f"Alert input did not contain a valid alert summary: {alert_json}"
            warnings.append(warning)
            return _malformed_alert(warning), source, warnings
        return payload, source, warnings

    latest_alert = _default_alert_path(snapshot_dir)
    if review_json is None and latest_alert.exists():
        payload, error = _load_json_object(latest_alert)
        source = {
            "input_kind": "latest_alert_json",
            "input_path": str(latest_alert),
            "snapshot_dir": str(snapshot_dir),
            "built_alert_summary": False,
        }
        if error:
            warnings.append(error)
            return _malformed_alert(error), source, warnings
        if _looks_like_alert(payload):
            return payload, source, warnings
        warning = f"Latest alert JSON did not contain a valid alert summary: {latest_alert}"
        warnings.append(warning)
        return _malformed_alert(warning), source, warnings

    summary = build_alert_summary(review_json=review_json, snapshot_dir=snapshot_dir)
    source = {
        "input_kind": "review_json" if review_json is not None else "snapshot_dir",
        "input_path": str(review_json) if review_json is not None else str(snapshot_dir),
        "snapshot_dir": str(snapshot_dir),
        "built_alert_summary": True,
    }
    return summary_to_dict(summary), source, warnings


def _looks_like_alert(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "overall_severity",
        "primary_reason",
        "blocked_reasons",
        "warn_reasons",
        "info_items",
        "risk_response_summary",
        "paper_state_summary",
    }
    return required.issubset(set(value))


def _malformed_alert(reason: str) -> dict[str, Any]:
    return {
        "generated_at": None,
        "mode": "paper_daily_alert_summary_read_only",
        "overall_severity": "BLOCKED",
        "primary_reason": "Alert summary input is missing or malformed.",
        "blocked_reasons": ["Alert summary input is missing or malformed.", reason],
        "warn_reasons": [],
        "info_items": [],
        "changed_fields": [],
        "new_risk_flags": [],
        "resolved_risk_flags": [],
        "data_freshness_summary": {},
        "signal_summary": {},
        "risk_response_summary": {"risk_level": "BLOCK", "risk_flags": ["alert_input_malformed"], "response_action": "BLOCK"},
        "paper_state_summary": {"paper_position_open": None, "paper_side": None, "paper_entry_time": None, "paper_entry_price": None},
        "recommended_human_action": [
            "Regenerate local paper reports from existing commands.",
            "Do not infer missing data.",
            "Keep paper mode only; do not trade.",
        ],
        "warnings": [reason],
        "safety": {
            "api_keys_required": False,
            "external_notifications_enabled": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
        },
    }


def build_operator_checklist(
    *,
    alert_json: str | Path | None = None,
    review_json: str | Path | None = None,
    snapshot_dir: str | Path = "runtime/daily_reviews",
    now: datetime | None = None,
) -> OperatorChecklist:
    alert, source, load_warnings = load_or_build_alert_summary(
        alert_json=alert_json,
        review_json=review_json,
        snapshot_dir=snapshot_dir,
    )
    severity = str(alert.get("overall_severity") or "BLOCKED")
    if severity not in {"INFO", "WARN", "BLOCKED"}:
        severity = "BLOCKED"
        load_warnings.append("Alert severity was not INFO, WARN, or BLOCKED.")
    checklist_items = _checklist_for_alert(alert, severity)
    exact_commands = _dedupe(
        [
            command
            for item in checklist_items
            for command in _str_list(item.get("commands"))
        ]
    )

    return OperatorChecklist(
        generated_at=_utc_now_iso(now),
        mode="paper_operator_checklist_read_only",
        safety={
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
            "external_notifications_enabled": False,
            "read_only_checklist": True,
            "executes_remediation": False,
            "refreshes_data_by_default": False,
            "runs_signal_by_default": False,
            "runs_daily_review_by_default": False,
        },
        source=source,
        severity=severity,
        primary_reason=str(alert.get("primary_reason") or "No primary reason supplied."),
        checklist_items=checklist_items,
        exact_commands=exact_commands,
        safety_boundaries=list(SAFETY_BOUNDARIES),
        alert_summary=_compact_alert(alert),
        warnings=_dedupe([*load_warnings, *_str_list(alert.get("warnings"))]),
    )


def _compact_alert(alert: dict[str, Any]) -> dict[str, Any]:
    return {
        "overall_severity": alert.get("overall_severity"),
        "primary_reason": alert.get("primary_reason"),
        "blocked_reasons": alert.get("blocked_reasons", []),
        "warn_reasons": alert.get("warn_reasons", []),
        "info_items": alert.get("info_items", []),
        "changed_fields": alert.get("changed_fields", []),
        "new_risk_flags": alert.get("new_risk_flags", []),
        "resolved_risk_flags": alert.get("resolved_risk_flags", []),
        "data_freshness_summary": alert.get("data_freshness_summary", {}),
        "signal_summary": alert.get("signal_summary", {}),
        "risk_response_summary": alert.get("risk_response_summary", {}),
        "paper_state_summary": alert.get("paper_state_summary", {}),
    }


def _checklist_item(
    step_id: str,
    title: str,
    detail: str,
    *,
    commands: list[str] | None = None,
    severity: str,
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "severity": severity,
        "title": title,
        "detail": detail,
        "commands": commands or [],
        "manual_only": True,
    }


def _checklist_for_alert(alert: dict[str, Any], severity: str) -> list[dict[str, Any]]:
    if severity == "INFO":
        return _info_checklist(alert)
    if severity == "WARN":
        return _warn_checklist(alert)
    return _blocked_checklist(alert)


def _info_checklist(alert: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _checklist_item(
            "INFO-01",
            "Confirm latest data is fresh.",
            "Review the paper status dashboard and confirm the latest BTCUSDT 4h candle is fresh.",
            commands=[COMMANDS["paper_status"]],
            severity="INFO",
        ),
        _checklist_item(
            "INFO-02",
            "Confirm latest signal, risk, and response.",
            "Verify the signal decision, risk flags, and response action remain expected for paper mode.",
            commands=[COMMANDS["paper_status"], COMMANDS["alert_summary"]],
            severity="INFO",
        ),
        _checklist_item(
            "INFO-03",
            "Confirm paper state.",
            "Verify paper position state, side, entry time, and entry price are expected.",
            commands=[COMMANDS["paper_status"]],
            severity="INFO",
        ),
        _checklist_item(
            "INFO-04",
            "Archive daily review.",
            "Archive a fresh daily dry-run review snapshot for audit continuity.",
            commands=[COMMANDS["daily_review"]],
            severity="INFO",
        ),
        _checklist_item(
            "INFO-05",
            "Keep observing.",
            "Continue paper-mode observation only; take no trading action.",
            commands=[COMMANDS["operator_checklist"]],
            severity="INFO",
        ),
    ]


def _warn_checklist(alert: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _checklist_item(
            "WARN-01",
            "Inspect changed fields.",
            f"Review changed fields: {_str_list(alert.get('changed_fields'))}.",
            commands=[COMMANDS["alert_summary"]],
            severity="WARN",
        ),
        _checklist_item(
            "WARN-02",
            "Inspect new and resolved risk flags.",
            (
                f"New risk flags: {_str_list(alert.get('new_risk_flags'))}; "
                f"resolved risk flags: {_str_list(alert.get('resolved_risk_flags'))}."
            ),
            commands=[COMMANDS["alert_summary"], COMMANDS["paper_status"]],
            severity="WARN",
        ),
        _checklist_item(
            "WARN-03",
            "Rerun paper status dashboard.",
            "Recompute the read-only paper status view before making any paper-mode interpretation.",
            commands=[COMMANDS["paper_status"]],
            severity="WARN",
        ),
        _checklist_item(
            "WARN-04",
            "Rerun daily review.",
            "Archive a new daily review after reviewing the warning state.",
            commands=[COMMANDS["daily_review"]],
            severity="WARN",
        ),
        _checklist_item(
            "WARN-05",
            "Refresh public data only if stale or near-stale.",
            "If the candle is stale or near-stale, manually refresh public BTC data; otherwise do not refresh unnecessarily.",
            commands=[COMMANDS["refresh_data"]],
            severity="WARN",
        ),
        _checklist_item(
            "WARN-06",
            "Do not change thresholds.",
            "Do not tune strategy thresholds or parameters to clear a warning.",
            commands=[],
            severity="WARN",
        ),
        _checklist_item(
            "WARN-07",
            "Do not promote to live trading.",
            "Keep paper mode only; no live-trading readiness is implied.",
            commands=[COMMANDS["operator_checklist"]],
            severity="WARN",
        ),
    ]


def _blocked_checklist(alert: dict[str, Any]) -> list[dict[str, Any]]:
    blocked_reasons = _str_list(alert.get("blocked_reasons"))
    risk_response = alert.get("risk_response_summary") if isinstance(alert.get("risk_response_summary"), dict) else {}
    risk_flags = set(_str_list(risk_response.get("risk_flags")))
    response_action = risk_response.get("response_action")
    risk_level = risk_response.get("risk_level")
    items = [
        _checklist_item(
            "BLOCKED-01",
            "Identify blocked reason.",
            f"Review blocked reasons: {blocked_reasons}.",
            commands=[COMMANDS["alert_summary"]],
            severity="BLOCKED",
        )
    ]

    if "stale_data" in risk_flags or any("stale_data" in reason for reason in blocked_reasons):
        items.append(
            _checklist_item(
                "BLOCKED-02",
                "Resolve stale data manually.",
                "Run the public no-key BTC data refresh, then rerun one signal check, status dashboard, daily review, and alert summary.",
                commands=[
                    COMMANDS["refresh_data"],
                    COMMANDS["run_signal_once"],
                    COMMANDS["paper_status"],
                    COMMANDS["daily_review"],
                    COMMANDS["alert_summary"],
                    COMMANDS["operator_checklist"],
                ],
                severity="BLOCKED",
            )
        )

    if response_action == "BLOCK" or any("response action is BLOCK" in reason for reason in blocked_reasons):
        items.append(
            _checklist_item(
                "BLOCKED-03",
                "Do not override BLOCK response.",
                "Inspect risk flags, do not override BLOCK, and do not create a paper or live entry.",
                commands=[COMMANDS["paper_status"], COMMANDS["alert_summary"]],
                severity="BLOCKED",
            )
        )

    if risk_level == "BLOCK" or any("risk level is BLOCK" in reason for reason in blocked_reasons):
        items.append(
            _checklist_item(
                "BLOCKED-04",
                "Treat BLOCK risk as no-action state.",
                "A BLOCK risk level means no paper entry and no live action should be taken.",
                commands=[COMMANDS["paper_status"]],
                severity="BLOCKED",
            )
        )

    if _has_malformed_or_missing_input(alert):
        items.append(
            _checklist_item(
                "BLOCKED-05",
                "Regenerate local paper reports.",
                "If inputs are missing or malformed, regenerate reports from existing paper commands and do not infer missing data.",
                commands=[
                    COMMANDS["run_signal_once"],
                    COMMANDS["paper_status"],
                    COMMANDS["daily_review"],
                    COMMANDS["alert_summary"],
                ],
                severity="BLOCKED",
            )
        )

    items.extend(
        [
            _checklist_item(
                "BLOCKED-06",
                "Keep paper position closed unless paper logic changes it.",
                "Do not manually force a paper entry. Let existing paper automation record entries only when its deterministic response is PAPER_LONG.",
                commands=[COMMANDS["paper_status"]],
                severity="BLOCKED",
            ),
            _checklist_item(
                "BLOCKED-07",
                "Do not trade.",
                "No exchange orders, no private APIs, no live position management, and no live-trading readiness.",
                commands=[COMMANDS["operator_checklist"]],
                severity="BLOCKED",
            ),
        ]
    )
    return items


def _has_malformed_or_missing_input(alert: dict[str, Any]) -> bool:
    text = " ".join(_str_list(alert.get("blocked_reasons")) + _str_list(alert.get("warnings"))).lower()
    return any(token in text for token in ("missing", "malformed", "could not be read", "did not contain a valid"))


def checklist_to_dict(checklist: OperatorChecklist) -> dict[str, Any]:
    return to_jsonable(asdict(checklist))


def checklist_json(checklist: OperatorChecklist) -> str:
    return json.dumps(checklist_to_dict(checklist), indent=2, sort_keys=True)


def format_text_checklist(checklist: OperatorChecklist) -> str:
    payload = checklist_to_dict(checklist)
    lines = [
        "BTC Paper Operator Checklist",
        f"generated_at: {payload['generated_at']}",
        f"mode: {payload['mode']}",
        f"severity: {payload['severity']}",
        f"primary_reason: {payload['primary_reason']}",
        "safety_boundaries:",
    ]
    lines.extend(f"- {boundary}" for boundary in payload["safety_boundaries"])
    lines.append("checklist:")
    for item in payload["checklist_items"]:
        lines.append(f"- {item['step_id']} {item['title']}: {item['detail']}")
        for command in item["commands"]:
            lines.append(f"  command: {command}")
    lines.append("exact_commands:")
    lines.extend(f"- {command}" for command in payload["exact_commands"])
    lines.append(f"warnings: {payload['warnings']}")
    return "\n".join(lines) + "\n"


def format_markdown_checklist(checklist: OperatorChecklist) -> str:
    payload = checklist_to_dict(checklist)
    lines = [
        "# BTC Paper Operator Checklist",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Severity: `{payload['severity']}`",
        f"- Primary reason: `{payload['primary_reason']}`",
        f"- External notifications enabled: `{payload['safety']['external_notifications_enabled']}`",
        f"- Live orders enabled: `{payload['safety']['live_orders_enabled']}`",
        "",
        "## Safety Boundaries",
        "",
    ]
    lines.extend(f"- {boundary}" for boundary in payload["safety_boundaries"])
    lines.extend(["", "## Checklist", ""])
    for item in payload["checklist_items"]:
        lines.append(f"- `{item['step_id']}` **{item['title']}**: {item['detail']}")
        for command in item["commands"]:
            lines.append(f"  - `{command}`")
    lines.extend(["", "## Exact Commands", ""])
    lines.extend(f"- `{command}`" for command in payload["exact_commands"])
    lines.extend(["", "## Warnings", ""])
    if payload["warnings"]:
        lines.extend(f"- {warning}" for warning in payload["warnings"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def write_checklist_json(checklist: OperatorChecklist, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(checklist_json(checklist) + "\n", encoding="utf-8")
    return target


def write_checklist_markdown(checklist: OperatorChecklist, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_markdown_checklist(checklist), encoding="utf-8")
    return target
