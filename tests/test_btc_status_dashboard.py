from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from btc_signal.config import BtcSignalConfig
from btc_signal.features import make_signal_feature_frame
from btc_signal.models import SignalDecision
from btc_signal.signal_engine import evaluate_feature_frame
from btc_signal.status_dashboard import build_paper_status_report, report_to_dict, summarize_data_freshness


ROOT = Path(__file__).resolve().parents[1]


def _write_ohlcv(path: Path, latest_timestamp: str = "2026-05-28T00:00:00+00:00") -> None:
    latest = pd.Timestamp(latest_timestamp)
    rows = []
    for offset in range(3, -1, -1):
        ts = latest - pd.Timedelta(hours=4 * offset)
        rows.append(
            {
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "open": 100.0 + offset,
                "high": 110.0 + offset,
                "low": 90.0 + offset,
                "close": 105.0 + offset,
                "volume": 10.0 + offset,
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def _state(open_position: bool = False) -> dict[str, Any]:
    return {
        "symbol": "BTCUSDT",
        "position_side": "LONG" if open_position else None,
        "entry_time": "2026-05-28T00:00:00+00:00" if open_position else None,
        "entry_price": 100.0 if open_position else None,
        "last_signal_time": "2026-05-28T00:00:00+00:00" if open_position else None,
        "paper_equity": 100000.0,
        "max_drawdown_seen": 0.0,
        "open_position": open_position,
        "notes": ["test fixture"],
    }


def _log_entry(
    *,
    run_at: str = "2026-05-28T01:00:00+00:00",
    signal_decision: str = "WAIT",
    signal_name: str | None = None,
    risk_level: str = "HIGH",
    risk_flags: list[str] | None = None,
    response_action: str = "WATCH",
) -> dict[str, Any]:
    return {
        "run_at": run_at,
        "mode": "paper_dry_run_only",
        "signal": {
            "timestamp": "2026-05-28T00:00:00+00:00",
            "decision": signal_decision,
            "signal_name": signal_name,
            "confidence_label": "weak",
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
        "paper_state": _state(False),
        "safety": {
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
        },
    }


def _write_jsonl(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n", encoding="utf-8")


def _signal_decision(timestamp: datetime, signal: bool = False) -> tuple[SignalDecision, pd.DataFrame]:
    frame = make_signal_feature_frame(timestamp=timestamp, signal=signal)
    return evaluate_feature_frame(frame, BtcSignalConfig()), frame


def test_dashboard_combines_data_signal_risk_monitoring_and_state(tmp_path: Path, monkeypatch) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    logs_dir = tmp_path / "logs"
    state_path = tmp_path / "paper_state.json"
    _write_ohlcv(data_path)
    _write_jsonl(
        logs_dir / "btc_signal_decisions_20260528.jsonl",
        [
            _log_entry(risk_flags=["extreme_distance_from_ema50"], response_action="WATCH"),
            _log_entry(
                run_at="2026-05-28T02:00:00+00:00",
                risk_level="LOW",
                risk_flags=[],
                response_action="WAIT",
            ),
        ],
    )
    state_path.write_text(json.dumps(_state(False)), encoding="utf-8")
    decision, feature_frame = _signal_decision(datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc), signal=False)
    monkeypatch.setattr("btc_signal.status_dashboard.generate_signal", lambda _cfg: (decision, feature_frame))

    cfg = BtcSignalConfig(root=tmp_path, data_path=data_path, log_dir=logs_dir, paper_state_path=state_path)
    report = build_paper_status_report(
        config=cfg,
        logs_dir=logs_dir,
        state_path=state_path,
        limit=10,
        now=datetime(2026, 5, 28, 4, 0, tzinfo=timezone.utc),
    )
    payload = report_to_dict(report)

    assert payload["mode"] == "paper_status_read_only"
    assert payload["safety"]["live_orders_enabled"] is False
    assert payload["data"]["row_count"] == 4
    assert payload["data"]["stale"] is False
    assert payload["latest_signal"]["decision"] in {"WAIT", "WATCH"}
    assert payload["latest_signal"]["long1_active"] is False
    assert payload["latest_signal"]["passed_condition_count"] == 9
    assert payload["latest_signal"]["missing_condition_count"] == 1
    assert payload["latest_response"]["action"] in {"WAIT", "WATCH"}
    assert payload["monitoring"]["total_log_entries_read"] == 2
    assert payload["monitoring"]["entries_summarized"] == 2
    assert payload["paper_state"]["open_position"] is False


def test_dashboard_handles_missing_logs(tmp_path: Path, monkeypatch) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    state_path = tmp_path / "paper_state.json"
    _write_ohlcv(data_path)
    state_path.write_text(json.dumps(_state(False)), encoding="utf-8")
    decision, feature_frame = _signal_decision(datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc), signal=False)
    monkeypatch.setattr("btc_signal.status_dashboard.generate_signal", lambda _cfg: (decision, feature_frame))

    cfg = BtcSignalConfig(root=tmp_path, data_path=data_path, paper_state_path=state_path)
    report = build_paper_status_report(
        config=cfg,
        logs_dir=tmp_path / "missing_logs",
        state_path=state_path,
        now=datetime(2026, 5, 28, 4, 0, tzinfo=timezone.utc),
    )
    payload = report_to_dict(report)

    assert payload["monitoring"]["total_log_entries_read"] == 0
    assert any("Missing decision log path" in warning for warning in payload["warnings"])


def test_dashboard_handles_missing_paper_state(tmp_path: Path, monkeypatch) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    logs_dir = tmp_path / "logs"
    _write_ohlcv(data_path)
    _write_jsonl(logs_dir / "btc_signal_decisions_20260528.jsonl", [_log_entry()])
    decision, feature_frame = _signal_decision(datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc), signal=False)
    monkeypatch.setattr("btc_signal.status_dashboard.generate_signal", lambda _cfg: (decision, feature_frame))

    cfg = BtcSignalConfig(root=tmp_path, data_path=data_path, log_dir=logs_dir)
    report = build_paper_status_report(
        config=cfg,
        logs_dir=logs_dir,
        state_path=tmp_path / "missing_state.json",
        now=datetime(2026, 5, 28, 4, 0, tzinfo=timezone.utc),
    )
    payload = report_to_dict(report)

    assert payload["paper_state"]["available"] is False
    assert any("Paper state file is missing" in warning for warning in payload["warnings"])


def test_dashboard_marks_stale_data_and_blocks_risk(tmp_path: Path, monkeypatch) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    state_path = tmp_path / "paper_state.json"
    _write_ohlcv(data_path, latest_timestamp="2026-05-27T00:00:00+00:00")
    state_path.write_text(json.dumps(_state(False)), encoding="utf-8")
    decision, feature_frame = _signal_decision(datetime(2026, 5, 27, 0, 0, tzinfo=timezone.utc), signal=True)
    monkeypatch.setattr("btc_signal.status_dashboard.generate_signal", lambda _cfg: (decision, feature_frame))

    cfg = BtcSignalConfig(root=tmp_path, data_path=data_path, paper_state_path=state_path, stale_after_hours=8.0)
    report = build_paper_status_report(
        config=cfg,
        logs_dir=tmp_path / "missing_logs",
        state_path=state_path,
        now=datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc),
    )
    payload = report_to_dict(report)

    assert payload["data"]["stale"] is True
    assert payload["data"]["status"] == "stale"
    assert "stale_data" in payload["latest_risk"]["risk_flags"]
    assert payload["latest_response"]["action"] == "BLOCK"


def test_dashboard_exposes_risk_flag_aggregation(tmp_path: Path, monkeypatch) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    logs_dir = tmp_path / "logs"
    state_path = tmp_path / "paper_state.json"
    _write_ohlcv(data_path)
    _write_jsonl(
        logs_dir / "btc_signal_decisions_20260528.jsonl",
        [
            _log_entry(risk_flags=["weekly_daily_regime_mismatch", "extreme_distance_from_ema50"]),
            _log_entry(
                run_at="2026-05-28T02:00:00+00:00",
                risk_flags=["extreme_distance_from_ema50"],
            ),
        ],
    )
    state_path.write_text(json.dumps(_state(False)), encoding="utf-8")
    decision, feature_frame = _signal_decision(datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc), signal=False)
    monkeypatch.setattr("btc_signal.status_dashboard.generate_signal", lambda _cfg: (decision, feature_frame))

    cfg = BtcSignalConfig(root=tmp_path, data_path=data_path, log_dir=logs_dir, paper_state_path=state_path)
    report = build_paper_status_report(
        config=cfg,
        logs_dir=logs_dir,
        state_path=state_path,
        now=datetime(2026, 5, 28, 4, 0, tzinfo=timezone.utc),
    )
    payload = report_to_dict(report)

    assert payload["monitoring"]["top_risk_flags"][0] == {"name": "extreme_distance_from_ema50", "count": 2}
    assert payload["monitoring"]["risk_level_counts"]["HIGH"] == 2


def test_data_freshness_summary_shape(tmp_path: Path) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    _write_ohlcv(data_path)
    cfg = BtcSignalConfig(root=tmp_path, data_path=data_path)

    summary, warnings = summarize_data_freshness(
        data_path,
        cfg,
        now=datetime(2026, 5, 28, 4, 0, tzinfo=timezone.utc),
    )

    assert warnings == []
    assert summary["csv_path"] == str(data_path)
    assert summary["row_count"] == 4
    assert summary["latest_candle_timestamp"] == "2026-05-28T00:00:00+00:00"
    assert summary["latest_candle_age_hours"] == 4.0
    assert summary["status"] == "fresh"


def test_status_cli_outputs_json(tmp_path: Path) -> None:
    data_path = tmp_path / "BTCUSDT_4h.csv"
    logs_dir = tmp_path / "logs"
    state_path = tmp_path / "paper_state.json"
    _write_ohlcv(data_path)
    _write_jsonl(logs_dir / "btc_signal_decisions_20260528.jsonl", [_log_entry()])
    state_path.write_text(json.dumps(_state(False)), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "report_btc_paper_status.py"),
            "--data-path",
            str(data_path),
            "--logs-dir",
            str(logs_dir),
            "--state-path",
            str(state_path),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "paper_status_read_only"
    assert payload["data"]["row_count"] == 4
    assert payload["monitoring"]["total_log_entries_read"] == 1
    assert payload["safety"]["live_orders_enabled"] is False
