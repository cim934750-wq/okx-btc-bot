from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from btc_signal.operator_checklist import (
    build_operator_checklist,
    checklist_to_dict,
    format_markdown_checklist,
)


ROOT = Path(__file__).resolve().parents[1]


def _alert(
    *,
    severity: str = "INFO",
    primary_reason: str = "Paper dry-run status is informational.",
    blocked_reasons: list[str] | None = None,
    warn_reasons: list[str] | None = None,
    info_items: list[str] | None = None,
    risk_flags: list[str] | None = None,
    risk_level: str = "LOW",
    response_action: str = "WAIT",
    changed_fields: list[str] | None = None,
    new_risk_flags: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "generated_at": "2026-06-01T00:00:00+00:00",
        "mode": "paper_daily_alert_summary_read_only",
        "overall_severity": severity,
        "primary_reason": primary_reason,
        "alert_items": [],
        "blocked_reasons": blocked_reasons or [],
        "warn_reasons": warn_reasons or [],
        "info_items": info_items or ["Data freshness status is fresh."],
        "changed_fields": changed_fields or [],
        "new_risk_flags": new_risk_flags or [],
        "resolved_risk_flags": [],
        "data_freshness_summary": {
            "data_path": "data/BTCUSDT_4h.csv",
            "row_count": 100,
            "latest_candle_timestamp": "2026-06-01T00:00:00+00:00",
            "latest_candle_age_hours": 4.0,
            "stale_status": "fresh",
        },
        "signal_summary": {
            "signal_decision": "WAIT",
            "long1_active": False,
            "confidence": "weak",
            "passed_condition_count": 4,
            "missing_condition_count": 6,
            "main_missing_conditions": ["daily_bull"],
        },
        "risk_response_summary": {
            "risk_level": risk_level,
            "risk_flags": [] if risk_flags is None else risk_flags,
            "response_action": response_action,
        },
        "paper_state_summary": {
            "paper_position_open": False,
            "paper_side": None,
            "paper_entry_time": None,
            "paper_entry_price": None,
        },
        "recommended_human_action": ["Keep paper mode only; do not trade."],
        "warnings": [],
        "safety": {
            "api_keys_required": False,
            "external_notifications_enabled": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
        },
    }


def _write_json(path: Path, payload: dict[str, Any] | str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _titles(payload: dict[str, Any]) -> list[str]:
    return [item["title"] for item in payload["checklist_items"]]


def test_info_checklist_generation(tmp_path: Path) -> None:
    alert_path = _write_json(tmp_path / "alert.json", _alert(severity="INFO"))

    payload = checklist_to_dict(build_operator_checklist(alert_json=alert_path))

    assert payload["severity"] == "INFO"
    assert "Confirm latest data is fresh." in _titles(payload)
    assert "Archive daily review." in _titles(payload)
    assert "No exchange orders are enabled." in payload["safety_boundaries"]


def test_warn_checklist_generation(tmp_path: Path) -> None:
    alert_path = _write_json(
        tmp_path / "alert.json",
        _alert(
            severity="WARN",
            primary_reason="Signal decision changed since the prior snapshot.",
            warn_reasons=["Signal decision changed since the prior snapshot."],
            changed_fields=["signal_decision"],
            new_risk_flags=["weekly_daily_regime_mismatch"],
        ),
    )

    payload = checklist_to_dict(build_operator_checklist(alert_json=alert_path))

    assert payload["severity"] == "WARN"
    assert "Inspect changed fields." in _titles(payload)
    assert "Do not change thresholds." in _titles(payload)
    assert "Do not promote to live trading." in _titles(payload)


def test_blocked_checklist_generation_with_stale_data(tmp_path: Path) -> None:
    alert_path = _write_json(
        tmp_path / "alert.json",
        _alert(
            severity="BLOCKED",
            primary_reason="stale_data risk flag is active.",
            blocked_reasons=["stale_data risk flag is active.", "Latest response action is BLOCK.", "Latest risk level is BLOCK."],
            risk_flags=["stale_data", "extreme_distance_from_ema50"],
            risk_level="BLOCK",
            response_action="BLOCK",
        ),
    )

    payload = checklist_to_dict(build_operator_checklist(alert_json=alert_path))

    assert payload["severity"] == "BLOCKED"
    assert "Resolve stale data manually." in _titles(payload)
    assert "Do not override BLOCK response." in _titles(payload)
    assert "python scripts/refresh_btcusdt_4h_data.py" in payload["exact_commands"]


def test_blocked_checklist_generation_with_malformed_alert_input(tmp_path: Path) -> None:
    bad_path = _write_json(tmp_path / "bad.json", "{not-json")

    payload = checklist_to_dict(build_operator_checklist(alert_json=bad_path))

    assert payload["severity"] == "BLOCKED"
    assert "Regenerate local paper reports." in _titles(payload)
    assert any("malformed" in reason for reason in payload["alert_summary"]["blocked_reasons"])


def test_exact_command_suggestions_present(tmp_path: Path) -> None:
    alert_path = _write_json(
        tmp_path / "alert.json",
        _alert(
            severity="BLOCKED",
            blocked_reasons=["stale_data risk flag is active.", "Latest response action is BLOCK."],
            risk_flags=["stale_data"],
            response_action="BLOCK",
        ),
    )

    payload = checklist_to_dict(build_operator_checklist(alert_json=alert_path))
    commands = payload["exact_commands"]

    assert "python scripts/refresh_btcusdt_4h_data.py" in commands
    assert "python scripts/run_btc_signal_once.py" in commands
    assert "python scripts/report_btc_paper_status.py" in commands
    assert "python scripts/review_btc_daily_dry_run.py" in commands
    assert "python scripts/summarize_btc_daily_alerts.py" in commands
    assert "python scripts/print_btc_operator_checklist.py" in commands


def test_json_output_shape(tmp_path: Path) -> None:
    alert_path = _write_json(tmp_path / "alert.json", _alert())

    payload = checklist_to_dict(build_operator_checklist(alert_json=alert_path))

    assert set(
        [
            "severity",
            "primary_reason",
            "checklist_items",
            "exact_commands",
            "safety_boundaries",
            "alert_summary",
        ]
    ).issubset(payload)


def test_markdown_rendering(tmp_path: Path) -> None:
    alert_path = _write_json(tmp_path / "alert.json", _alert(severity="WARN", warn_reasons=["warning"]))

    markdown = format_markdown_checklist(build_operator_checklist(alert_json=alert_path))

    assert "# BTC Paper Operator Checklist" in markdown
    assert "## Safety Boundaries" in markdown
    assert "## Exact Commands" in markdown


def test_operator_checklist_cli_outputs_json(tmp_path: Path) -> None:
    alert_path = _write_json(tmp_path / "alert.json", _alert())

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "print_btc_operator_checklist.py"),
            "--alert-json",
            str(alert_path),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "paper_operator_checklist_read_only"
    assert payload["severity"] == "INFO"
    assert payload["safety"]["live_orders_enabled"] is False
