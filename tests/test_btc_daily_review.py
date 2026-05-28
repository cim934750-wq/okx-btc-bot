from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from btc_signal.config import BtcSignalConfig
from btc_signal.daily_review import (
    build_daily_review,
    compare_snapshots,
    load_previous_snapshot,
    review_to_dict,
    snapshot_from_status_report,
)
from btc_signal.status_dashboard import PaperStatusReport


ROOT = Path(__file__).resolve().parents[1]


def _status_report(
    *,
    generated_at: str = "2026-05-28T05:00:00+00:00",
    stale_status: str = "fresh",
    signal_decision: str = "WAIT",
    long1_active: bool = False,
    confidence: str = "weak",
    passed_count: int = 4,
    missing_count: int = 6,
    missing_conditions: list[str] | None = None,
    risk_level: str = "HIGH",
    risk_flags: list[str] | None = None,
    response_action: str = "WATCH",
    paper_open: bool = False,
    paper_side: str | None = None,
    monitoring_total: int = 2,
    stale_data_count: int = 0,
    warnings: list[str] | None = None,
) -> PaperStatusReport:
    missing = ["daily_bull", "exec_bull_structure", "exec_slope_up"] if missing_conditions is None else missing_conditions
    flags = ["extreme_distance_from_ema50"] if risk_flags is None else risk_flags
    return PaperStatusReport(
        generated_at=generated_at,
        mode="paper_status_read_only",
        safety={
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
            "read_only_report": True,
            "refreshes_data_by_default": False,
        },
        data={
            "csv_path": "data/BTCUSDT_4h.csv",
            "available": True,
            "row_count": 100,
            "latest_candle_timestamp": "2026-05-28T00:00:00+00:00",
            "latest_candle_age_hours": 5.0,
            "latest_candle_complete": True,
            "stale_after_hours": 8.0,
            "stale": stale_status == "stale",
            "status": stale_status,
            "validation_error": None,
        },
        latest_signal={
            "available": True,
            "timestamp": "2026-05-28T00:00:00+00:00",
            "decision": signal_decision,
            "long1_active": long1_active,
            "signal_name": "Long1" if long1_active else None,
            "confidence_label": confidence,
            "passed_condition_count": passed_count,
            "missing_condition_count": missing_count,
            "main_missing_conditions": missing,
            "passed_conditions": ["weekly_bull"],
            "missing_conditions": missing,
            "evidence": {"close": 100.0},
            "reasoning_summary": "test fixture",
        },
        latest_risk={
            "risk_level": risk_level,
            "risk_flags": flags,
            "blocked_reason": None,
            "warnings": [],
        },
        latest_response={
            "action": response_action,
            "reason": "test fixture",
            "required_user_action": None,
            "should_log": True,
            "should_notify": False,
        },
        monitoring={
            "total_log_entries_read": monitoring_total,
            "entries_summarized": min(monitoring_total, 20),
            "signal_decision_counts": {"WAIT": monitoring_total, "WATCH": 0, "LONG_SIGNAL": 0, "BLOCKED": 0},
            "response_action_counts": {"WAIT": 0, "WATCH": monitoring_total, "PAPER_LONG": 0, "BLOCK": 0, "EXIT_WARNING": 0},
            "risk_level_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": monitoring_total, "BLOCK": 0},
            "stale_data_flag_count": stale_data_count,
            "top_risk_flags": [{"name": flags[0], "count": monitoring_total}] if flags else [],
            "latest_decision": None,
            "warnings": [],
            "files_read": [],
        },
        paper_state={
            "source": "runtime/paper_state.json",
            "available": True,
            "open_position": paper_open,
            "position_side": paper_side,
            "entry_time": "2026-05-28T00:00:00+00:00" if paper_open else None,
            "entry_price": 100.0 if paper_open else None,
            "last_signal_time": None,
            "paper_equity": 100000.0,
            "max_drawdown_seen": 0.0,
            "notes_count": 1,
        },
        warnings=warnings or [],
    )


def _write_minimal_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2026-05-28T00:00:00+00:00,100,110,90,105,10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def test_snapshot_generation_from_normal_dashboard_data() -> None:
    snapshot = snapshot_from_status_report(_status_report())

    assert snapshot["review_timestamp_utc"] == "2026-05-28T05:00:00+00:00"
    assert snapshot["data_path"] == "data/BTCUSDT_4h.csv"
    assert snapshot["row_count"] == 100
    assert snapshot["signal_decision"] == "WAIT"
    assert snapshot["risk_level"] == "HIGH"
    assert snapshot["response_action"] == "WATCH"
    assert snapshot["paper_position_open"] is False
    assert snapshot["monitoring_total_entries"] == 2


def test_missing_previous_snapshot_is_graceful(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("btc_signal.daily_review.build_paper_status_report", lambda **_kwargs: _status_report())

    review = build_daily_review(
        config=BtcSignalConfig(root=tmp_path, data_path=tmp_path / "missing.csv"),
        snapshot_dir=tmp_path / "daily_reviews",
    )
    payload = review_to_dict(review)

    assert payload["comparison"]["previous_available"] is False
    assert payload["comparison"]["summary"] == "No previous snapshot available for comparison."
    assert Path(payload["output_paths"]["snapshot_latest_json"]).exists()
    assert Path(payload["output_paths"]["snapshot_timestamped_json"]).exists()


def test_comparison_flags_changed_signal_and_risk_flags() -> None:
    previous = snapshot_from_status_report(
        _status_report(signal_decision="WAIT", risk_level="LOW", risk_flags=[])
    )
    current = snapshot_from_status_report(
        _status_report(
            signal_decision="LONG_SIGNAL",
            long1_active=True,
            confidence="strong",
            passed_count=10,
            missing_count=0,
            missing_conditions=[],
            risk_level="HIGH",
            risk_flags=["extreme_distance_from_ema50", "weekly_daily_regime_mismatch"],
            response_action="BLOCK",
        )
    )

    comparison = compare_snapshots(current, previous)

    assert comparison["signal_decision_changed"] is True
    assert comparison["long1_active_changed"] is True
    assert comparison["risk_level_changed"] is True
    assert comparison["response_action_changed"] is True
    assert comparison["new_risk_flags"] == ["extreme_distance_from_ema50", "weekly_daily_regime_mismatch"]
    assert "daily_bull" in comparison["resolved_missing_conditions"]


def test_comparison_flags_changed_paper_state() -> None:
    previous = snapshot_from_status_report(_status_report(paper_open=False, paper_side=None))
    current = snapshot_from_status_report(_status_report(paper_open=True, paper_side="LONG"))

    comparison = compare_snapshots(current, previous)

    assert comparison["paper_position_change"] == "opened"
    assert comparison["paper_side_changed"] is True
    assert "paper_position_open" in comparison["changed_fields"]


def test_comparison_flags_stale_status_change() -> None:
    previous = snapshot_from_status_report(_status_report(stale_status="fresh"))
    current = snapshot_from_status_report(_status_report(stale_status="stale", risk_flags=["stale_data"]))

    comparison = compare_snapshots(current, previous)

    assert comparison["stale_status_changed"] is True
    assert "stale_status" in comparison["changed_fields"]
    assert comparison["new_risk_flags"] == ["stale_data"]


def test_malformed_previous_snapshot_handling(tmp_path: Path) -> None:
    bad = tmp_path / "bad_snapshot.json"
    bad.write_text("{not-json", encoding="utf-8")

    previous, warnings = load_previous_snapshot(bad)
    comparison = compare_snapshots(snapshot_from_status_report(_status_report()), previous, previous_path=bad, load_warnings=warnings)

    assert previous is None
    assert comparison["previous_available"] is False
    assert any("could not be read" in warning for warning in comparison["warnings"])


def test_daily_review_cli_outputs_json_and_writes_snapshots(tmp_path: Path) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    logs_dir = tmp_path / "logs"
    state_path = tmp_path / "paper_state.json"
    snapshot_dir = tmp_path / "daily_reviews"
    _write_minimal_csv(data_path)
    _write_jsonl(
        logs_dir / "btc_signal_decisions_20260528.jsonl",
        {
            "run_at": "2026-05-28T05:00:00+00:00",
            "signal": {"timestamp": "2026-05-28T00:00:00+00:00", "decision": "WAIT"},
            "risk": {"risk_level": "HIGH", "risk_flags": ["test_flag"]},
            "response": {"action": "WATCH"},
            "paper_state": {"open_position": False},
        },
    )
    state_path.write_text(
        json.dumps(
            {
                "symbol": "BTCUSDT",
                "position_side": None,
                "entry_time": None,
                "entry_price": None,
                "last_signal_time": None,
                "paper_equity": 100000.0,
                "max_drawdown_seen": 0.0,
                "open_position": False,
                "notes": [],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "review_btc_daily_dry_run.py"),
            "--data-path",
            str(data_path),
            "--logs-dir",
            str(logs_dir),
            "--state-path",
            str(state_path),
            "--snapshot-dir",
            str(snapshot_dir),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "paper_daily_review_read_only"
    assert payload["safety"]["live_orders_enabled"] is False
    assert payload["comparison"]["previous_available"] is False
    assert (snapshot_dir / "btc_daily_review_latest.json").exists()
