from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from btc_signal.alert_summary import build_alert_summary, summary_to_dict


ROOT = Path(__file__).resolve().parents[1]


def _snapshot(
    *,
    stale_status: str = "fresh",
    age: float = 4.0,
    signal_decision: str = "WAIT",
    long1_active: bool = False,
    confidence: str = "weak",
    risk_level: str = "LOW",
    risk_flags: list[str] | None = None,
    response_action: str = "WAIT",
    paper_open: bool = False,
    paper_side: str | None = None,
    paper_entry_time: str | None = None,
    paper_entry_price: float | None = None,
    monitoring_total: int = 2,
    stale_data_count: int = 0,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "review_timestamp_utc": "2026-05-28T05:00:00+00:00",
        "data_path": "data/BTCUSDT_4h.csv",
        "row_count": 100,
        "latest_candle_timestamp": "2026-05-28T00:00:00+00:00",
        "latest_candle_age_hours": age,
        "stale_status": stale_status,
        "signal_decision": signal_decision,
        "long1_active": long1_active,
        "confidence": confidence,
        "passed_condition_count": 4,
        "missing_condition_count": 6,
        "main_missing_conditions": ["daily_bull"],
        "risk_level": risk_level,
        "risk_flags": [] if risk_flags is None else risk_flags,
        "response_action": response_action,
        "paper_position_open": paper_open,
        "paper_side": paper_side,
        "paper_entry_time": paper_entry_time,
        "paper_entry_price": paper_entry_price,
        "monitoring_total_entries": monitoring_total,
        "monitoring_entries_summarized": min(monitoring_total, 20),
        "monitoring_signal_counts": {"WAIT": monitoring_total, "WATCH": 0, "LONG_SIGNAL": 0, "BLOCKED": 0},
        "monitoring_response_counts": {"WAIT": monitoring_total, "WATCH": 0, "PAPER_LONG": 0, "BLOCK": 0, "EXIT_WARNING": 0},
        "monitoring_risk_counts": {"LOW": monitoring_total, "MEDIUM": 0, "HIGH": 0, "BLOCK": 0},
        "monitoring_stale_data_count": stale_data_count,
        "monitoring_top_risk_flags": [],
        "warnings": [] if warnings is None else warnings,
    }


def _review(snapshot: dict[str, Any], comparison: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "generated_at": snapshot["review_timestamp_utc"],
        "mode": "paper_daily_review_read_only",
        "snapshot": snapshot,
        "comparison": comparison or {
            "previous_available": True,
            "summary": "No compared fields changed.",
            "changed_fields": [],
            "new_risk_flags": [],
            "resolved_risk_flags": [],
            "signal_decision_changed": False,
            "long1_active_changed": False,
            "confidence_changed": False,
            "risk_level_changed": False,
            "response_action_changed": False,
            "paper_position_change": "unchanged",
            "monitoring_log_count": {"previous": 1, "current": 2, "delta": 1, "changed": True},
            "monitoring_stale_data_count": {"previous": 0, "current": 0, "delta": 0, "changed": False},
            "warning_count": {"previous": 0, "current": len(snapshot.get("warnings", [])), "delta": 0, "changed": False},
        },
        "warnings": snapshot.get("warnings", []),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_fresh_healthy_case_is_info(tmp_path: Path) -> None:
    review_path = _write_json(tmp_path / "review.json", _review(_snapshot()))

    summary = build_alert_summary(review_json=review_path)
    payload = summary_to_dict(summary)

    assert payload["overall_severity"] == "INFO"
    assert payload["blocked_reasons"] == []
    assert "Data freshness status is fresh." in payload["info_items"]
    assert payload["safety"]["external_notifications_enabled"] is False


def test_stale_data_flag_is_blocked(tmp_path: Path) -> None:
    review_path = _write_json(
        tmp_path / "review.json",
        _review(_snapshot(stale_status="stale", age=9.0, risk_level="BLOCK", risk_flags=["stale_data"], response_action="BLOCK")),
    )

    payload = summary_to_dict(build_alert_summary(review_json=review_path))

    assert payload["overall_severity"] == "BLOCKED"
    assert "stale_data risk flag is active." in payload["blocked_reasons"]


def test_response_block_is_blocked(tmp_path: Path) -> None:
    review_path = _write_json(tmp_path / "review.json", _review(_snapshot(response_action="BLOCK")))

    payload = summary_to_dict(build_alert_summary(review_json=review_path))

    assert payload["overall_severity"] == "BLOCKED"
    assert "Latest response action is BLOCK." in payload["blocked_reasons"]


def test_missing_snapshot_is_blocked(tmp_path: Path) -> None:
    payload = summary_to_dict(build_alert_summary(snapshot_dir=tmp_path / "missing"))

    assert payload["overall_severity"] == "BLOCKED"
    assert any("missing or malformed" in reason for reason in payload["blocked_reasons"])


def test_changed_signal_is_warn(tmp_path: Path) -> None:
    review_path = _write_json(
        tmp_path / "review.json",
        _review(
            _snapshot(signal_decision="WATCH"),
            {
                "previous_available": True,
                "changed_fields": ["signal_decision"],
                "new_risk_flags": [],
                "resolved_risk_flags": [],
                "signal_decision_changed": True,
                "long1_active_changed": False,
                "confidence_changed": False,
                "paper_position_change": "unchanged",
                "monitoring_log_count": {"previous": 1, "current": 2, "delta": 1},
                "warning_count": {"previous": 0, "current": 0, "delta": 0},
            },
        ),
    )

    payload = summary_to_dict(build_alert_summary(review_json=review_path))

    assert payload["overall_severity"] == "WARN"
    assert "Signal decision changed since the prior snapshot." in payload["warn_reasons"]


def test_new_risk_flag_warn_or_blocked_by_flag_type(tmp_path: Path) -> None:
    warn_review = _write_json(
        tmp_path / "warn.json",
        _review(
            _snapshot(risk_level="HIGH", risk_flags=["weekly_daily_regime_mismatch"], response_action="WATCH"),
            {"previous_available": True, "new_risk_flags": ["weekly_daily_regime_mismatch"], "changed_fields": ["risk_flags"]},
        ),
    )
    blocked_review = _write_json(
        tmp_path / "blocked.json",
        _review(
            _snapshot(stale_status="stale", risk_level="BLOCK", risk_flags=["stale_data"], response_action="WATCH"),
            {"previous_available": True, "new_risk_flags": ["stale_data"], "changed_fields": ["risk_flags"]},
        ),
    )

    warn_payload = summary_to_dict(build_alert_summary(review_json=warn_review))
    blocked_payload = summary_to_dict(build_alert_summary(review_json=blocked_review))

    assert warn_payload["overall_severity"] == "WARN"
    assert "weekly_daily_regime_mismatch" in warn_payload["warn_reasons"][0]
    assert blocked_payload["overall_severity"] == "BLOCKED"
    assert any("New blocking risk flag" in reason for reason in blocked_payload["blocked_reasons"])


def test_malformed_input_is_blocked(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json", encoding="utf-8")

    payload = summary_to_dict(build_alert_summary(review_json=bad_path))

    assert payload["overall_severity"] == "BLOCKED"
    assert any("could not be read" in reason for reason in payload["blocked_reasons"])


def test_json_output_shape(tmp_path: Path) -> None:
    review_path = _write_json(tmp_path / "review.json", _review(_snapshot()))

    payload = summary_to_dict(build_alert_summary(review_json=review_path))

    assert set(
        [
            "overall_severity",
            "primary_reason",
            "alert_items",
            "data_freshness_summary",
            "signal_summary",
            "risk_response_summary",
            "paper_state_summary",
            "recommended_human_action",
        ]
    ).issubset(payload)


def test_alert_summary_cli_outputs_json(tmp_path: Path) -> None:
    review_path = _write_json(tmp_path / "review.json", _review(_snapshot()))

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "summarize_btc_daily_alerts.py"),
            "--review-json",
            str(review_path),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "paper_daily_alert_summary_read_only"
    assert payload["overall_severity"] == "INFO"
    assert payload["safety"]["live_orders_enabled"] is False
