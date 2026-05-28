from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from btc_signal.monitoring import build_monitoring_report, report_to_dict


ROOT = Path(__file__).resolve().parents[1]


def _state(open_position: bool = False, entry_time: str | None = None) -> dict[str, Any]:
    return {
        "symbol": "BTCUSDT",
        "position_side": "LONG" if open_position else None,
        "entry_time": entry_time,
        "entry_price": 100.0 if open_position else None,
        "last_signal_time": entry_time,
        "paper_equity": 100000.0,
        "max_drawdown_seen": 0.0,
        "open_position": open_position,
        "notes": ["test fixture"],
    }


def _entry(
    *,
    run_at: str = "2026-05-28T01:00:00+00:00",
    signal_timestamp: str = "2026-05-28T00:00:00+00:00",
    signal_decision: str = "WAIT",
    signal_name: str | None = None,
    risk_level: str = "LOW",
    risk_flags: list[str] | None = None,
    response_action: str = "WAIT",
    paper_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "run_at": run_at,
        "mode": "paper_dry_run_only",
        "signal": {
            "timestamp": signal_timestamp,
            "decision": signal_decision,
            "signal_name": signal_name,
            "confidence_label": "strong" if signal_name == "Long1" else "weak",
            "evidence": {"close": 100.0},
        },
        "risk": {
            "risk_level": risk_level,
            "risk_flags": risk_flags or [],
            "blocked_reason": None,
            "warnings": [],
        },
        "response": {
            "action": response_action,
            "reason": "test fixture",
            "required_user_action": None,
            "should_log": True,
            "should_notify": False,
        },
        "paper_state": paper_state or _state(False),
        "safety": {
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
        },
    }


def _write_jsonl(path: Path, entries: list[dict[str, Any]], extra_lines: list[str] | None = None) -> None:
    lines = [json.dumps(entry, sort_keys=True) for entry in entries]
    lines.extend(extra_lines or [])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_missing_logs_and_state_are_reported_gracefully(tmp_path: Path) -> None:
    report = build_monitoring_report(
        logs_dir=tmp_path / "missing_logs",
        state_path=tmp_path / "missing_state.json",
        now=None,
    )
    payload = report_to_dict(report)

    assert payload["metrics"]["total_log_entries_read"] == 0
    assert payload["metrics"]["entries_summarized"] == 0
    assert payload["paper_state"]["available"] is False
    assert any("Missing decision log path" in warning for warning in payload["warnings"])
    assert any("Missing paper state path" in warning for warning in payload["warnings"])


def test_malformed_jsonl_line_is_skipped(tmp_path: Path) -> None:
    log_path = tmp_path / "btc_signal_decisions_20260528.jsonl"
    _write_jsonl(log_path, [_entry()], extra_lines=["{not-json"])

    report = build_monitoring_report(log_path=log_path, state_path=None)
    payload = report_to_dict(report)

    assert payload["metrics"]["total_log_entries_read"] == 1
    assert payload["metrics"]["malformed_line_count"] == 1
    assert any("Malformed JSONL line skipped" in warning for warning in payload["warnings"])


def test_monitoring_report_aggregates_counts_and_top_risk_flags(tmp_path: Path) -> None:
    log_path = tmp_path / "btc_signal_decisions_20260528.jsonl"
    _write_jsonl(
        log_path,
        [
            _entry(
                run_at="2026-05-28T01:00:00+00:00",
                risk_level="HIGH",
                risk_flags=["extreme_distance_from_ema50"],
                response_action="WATCH",
            ),
            _entry(
                run_at="2026-05-28T02:00:00+00:00",
                signal_decision="LONG_SIGNAL",
                signal_name="Long1",
                risk_level="LOW",
                response_action="PAPER_LONG",
                paper_state=_state(True, "2026-05-28T00:00:00+00:00"),
            ),
            _entry(
                run_at="2026-05-28T03:00:00+00:00",
                risk_level="BLOCK",
                risk_flags=["stale_data", "extreme_distance_from_ema50"],
                response_action="BLOCK",
                paper_state=_state(True, "2026-05-28T00:00:00+00:00"),
            ),
        ],
    )

    report = build_monitoring_report(log_path=log_path, state_path=None, limit=3)
    payload = report_to_dict(report)
    metrics = payload["metrics"]

    assert metrics["signal_decision_counts"]["WAIT"] == 2
    assert metrics["signal_decision_counts"]["LONG_SIGNAL"] == 1
    assert metrics["response_action_counts"]["WATCH"] == 1
    assert metrics["response_action_counts"]["PAPER_LONG"] == 1
    assert metrics["response_action_counts"]["BLOCK"] == 1
    assert metrics["risk_level_counts"]["HIGH"] == 1
    assert metrics["risk_level_counts"]["BLOCK"] == 1
    assert metrics["long1_active_count"] == 1
    assert metrics["paper_long_count"] == 1
    assert metrics["stale_data_flag_count"] == 1
    assert metrics["top_risk_flags"][0] == {"name": "extreme_distance_from_ema50", "count": 2}


def test_paper_state_summary_and_changes_are_inferred(tmp_path: Path) -> None:
    log_path = tmp_path / "btc_signal_decisions_20260528.jsonl"
    state_path = tmp_path / "paper_state.json"
    closed_state = _state(False)
    open_state = _state(True, "2026-05-28T00:00:00+00:00")
    _write_jsonl(
        log_path,
        [
            _entry(run_at="2026-05-28T01:00:00+00:00", paper_state=closed_state),
            _entry(run_at="2026-05-28T02:00:00+00:00", paper_state=open_state),
        ],
    )
    state_path.write_text(json.dumps(open_state), encoding="utf-8")

    report = build_monitoring_report(log_path=log_path, state_path=state_path)
    payload = report_to_dict(report)

    assert payload["paper_state"]["available"] is True
    assert payload["paper_state"]["open_position"] is True
    assert payload["paper_state"]["position_side"] == "LONG"
    assert payload["metrics"]["paper_state_change_count"] == 1
    assert "open_position" in payload["paper_state_changes"][0]["changed_fields"]


def test_report_cli_outputs_json(tmp_path: Path) -> None:
    log_path = tmp_path / "btc_signal_decisions_20260528.jsonl"
    state_path = tmp_path / "paper_state.json"
    _write_jsonl(log_path, [_entry(response_action="WATCH")])
    state_path.write_text(json.dumps(_state(False)), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "report_btc_dry_run_status.py"),
            "--log-path",
            str(log_path),
            "--state-path",
            str(state_path),
            "--limit",
            "1",
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "paper_dry_run_monitoring_only"
    assert payload["metrics"]["entries_summarized"] == 1
    assert payload["metrics"]["watch_count"] == 1
    assert payload["safety"]["live_orders_enabled"] is False
