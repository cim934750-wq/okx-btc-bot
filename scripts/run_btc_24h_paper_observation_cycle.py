#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SAFE_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("scripts/refresh_btcusdt_4h_data.py",),
    ("scripts/run_btc_signal_once.py",),
    ("scripts/report_btc_paper_status.py", "--format", "json"),
    ("scripts/report_btc_dry_run_status.py", "--format", "json"),
    ("scripts/review_btc_daily_dry_run.py", "--format", "json"),
    ("scripts/summarize_btc_daily_alerts.py", "--format", "json"),
    ("scripts/print_btc_operator_checklist.py", "--format", "json"),
    ("scripts/audit_btc_order_intent_schema.py", "--format", "json"),
    ("scripts/review_btc_order_intent_writer_design.py", "--format", "json"),
)

COMMAND_LABELS: tuple[str, ...] = (
    "refresh",
    "signal",
    "paper_status",
    "monitoring",
    "daily_review",
    "alert_summary",
    "operator_checklist",
    "schema_audit",
    "writer_review",
)


@dataclass(slots=True)
class CommandResult:
    label: str
    command: list[str]
    exit_code: int
    stdout_path: str | None
    stderr_path: str | None
    timed_out: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a local or VM BTC paper observation cycle using existing safe paper-mode commands only. "
            "No private APIs, order intents, adapters, testnet, or live trading are used."
        )
    )
    parser.add_argument("--duration-hours", type=float, default=24.0, help="Observation duration. Default: 24.")
    parser.add_argument(
        "--interval-minutes",
        type=float,
        default=245.0,
        help="Delay between cycles. Default: 245 minutes, about 4h5m.",
    )
    parser.add_argument("--output-dir", default="runtime/observation", help="Runtime observation output directory.")
    parser.add_argument("--once", action="store_true", help="Run one cycle and stop.")
    parser.add_argument(
        "--no-sleep",
        action="store_true",
        help="Do not sleep after a cycle. Intended for local tests; it stops after one cycle.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the safe command plan without running commands.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument(
        "--command-timeout-seconds",
        type=int,
        default=300,
        help="Timeout for each safe command. Default: 300.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run safe command scripts. Default: current interpreter.",
    )
    return parser


def safe_command_plan(python_executable: str) -> list[list[str]]:
    return [[python_executable, *command] for command in SAFE_COMMANDS]


def safety_boundary() -> dict[str, bool]:
    return {
        "paper_observation_only": True,
        "okx_public_market_data_only": True,
        "api_keys_required": False,
        "private_api_calls": False,
        "account_reads": False,
        "order_placement": False,
        "order_intent_writer": False,
        "runtime_order_intents": False,
        "exchange_adapter": False,
        "simulated_adapter": False,
        "testnet_trading": False,
        "live_trading": False,
        "external_notifications": False,
    }


def run_observation(args: argparse.Namespace) -> dict[str, Any]:
    started_at = now_utc()
    command_plan = safe_command_plan(args.python)
    payload: dict[str, Any] = {
        "mode": "btc_paper_observation_cycle",
        "started_at_utc": isoformat_z(started_at),
        "duration_hours": args.duration_hours,
        "interval_minutes": args.interval_minutes,
        "dry_run": args.dry_run,
        "once": args.once,
        "no_sleep": args.no_sleep,
        "safe_commands": command_plan,
        "safety": safety_boundary(),
    }

    if args.dry_run:
        payload.update(
            {
                "completed_at_utc": isoformat_z(now_utc()),
                "completed_24h": False,
                "cycles_completed": 0,
                "command_results": [],
                "summary": "Dry run only; no safe commands were executed and no runtime files were written.",
            }
        )
        return payload

    output_root = resolve_path(args.output_dir)
    run_dir = output_root / f"btc_24h_vm_observation_{timestamp_for_path(started_at)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (output_root / "btc_24h_vm_observation_latest_dir.txt").write_text(str(run_dir) + "\n", encoding="utf-8")

    deadline = started_at.timestamp() + max(0.0, args.duration_hours) * 3600.0
    cycle_results: list[list[CommandResult]] = []
    cycle_index = 0

    while True:
        cycle_label = "final" if now_utc().timestamp() >= deadline and cycle_index > 0 else f"cycle_{cycle_index:03d}"
        cycle_results.append(run_cycle(cycle_label, command_plan, run_dir, args.command_timeout_seconds))
        write_summary(output_root, run_dir, started_at, args, cycle_results)
        cycle_index += 1

        if args.once or args.no_sleep:
            break

        now = now_utc().timestamp()
        if now >= deadline:
            break

        sleep_seconds = min(max(0.0, args.interval_minutes) * 60.0, max(0.0, deadline - now))
        if sleep_seconds <= 0:
            break
        time.sleep(sleep_seconds)

    summary = build_summary(run_dir, started_at, args, cycle_results)
    write_summary_files(output_root, summary)
    return summary


def run_cycle(
    cycle_label: str,
    command_plan: list[list[str]],
    run_dir: Path,
    timeout_seconds: int,
) -> list[CommandResult]:
    cycle_dir = run_dir / cycle_label
    cycle_dir.mkdir(parents=True, exist_ok=True)
    results: list[CommandResult] = []
    for label, command in zip(COMMAND_LABELS, command_plan):
        stdout_path = cycle_dir / f"{label}.json"
        stderr_path = cycle_dir / f"{label}.err"
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            stdout_path.write_bytes(completed.stdout)
            stderr_path.write_bytes(completed.stderr)
            timed_out = False
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_bytes(exc.stdout or b"")
            stderr_path.write_bytes(
                (exc.stderr or b"")
                + f"\nCommand timed out after {timeout_seconds} seconds: {' '.join(command)}\n".encode()
            )
            timed_out = True
            exit_code = 124
        (cycle_dir / f"{label}.exit").write_text(str(exit_code) + "\n", encoding="utf-8")
        results.append(
            CommandResult(
                label=label,
                command=command,
                exit_code=exit_code,
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                timed_out=timed_out,
            )
        )
    return results


def build_summary(
    run_dir: Path,
    started_at: datetime,
    args: argparse.Namespace,
    cycle_results: list[list[CommandResult]],
) -> dict[str, Any]:
    completed_at = now_utc()
    elapsed_hours = (completed_at - started_at).total_seconds() / 3600.0
    command_results = [[asdict(result) for result in cycle] for cycle in cycle_results]
    parsed_outputs = parse_observation_outputs(run_dir)
    completed_24h = elapsed_hours >= 24.0

    summary = {
        "mode": "btc_paper_observation_cycle",
        "run_dir": str(run_dir),
        "started_at_utc": isoformat_z(started_at),
        "completed_at_utc": isoformat_z(completed_at),
        "duration_hours": args.duration_hours,
        "elapsed_hours": round(elapsed_hours, 4),
        "completed_24h": completed_24h,
        "cycles_completed": len(cycle_results),
        "command_results": command_results,
        "safe_commands": safe_command_plan(args.python),
        "safety": {
            **safety_boundary(),
            "runtime_order_intents_exists": (ROOT / "runtime/order_intents").exists(),
        },
        **parsed_outputs,
    }
    return summary


def parse_observation_outputs(run_dir: Path) -> dict[str, Any]:
    signal_counts: Counter[str] = Counter()
    response_counts: Counter[str] = Counter()
    risk_level_counts: Counter[str] = Counter()
    risk_flag_counts: Counter[str] = Counter()
    alert_counts: Counter[str] = Counter()
    checklist_counts: Counter[str] = Counter()
    stale_data_count = 0
    long1_count = 0
    paper_long_count = 0
    block_count = 0
    malformed_outputs = 0
    latest_candle: dict[str, Any] = {}
    latest_paper_state: dict[str, Any] = {}

    refresh_attempts = len(list(run_dir.glob("cycle_*/refresh.json"))) + len(list(run_dir.glob("final/refresh.json")))
    refresh_success = 0
    refresh_failure = 0
    old_latest = None
    new_latest = None

    for path in sorted(run_dir.glob("*/refresh.json")):
        data = load_json(path)
        if data is None:
            malformed_outputs += 1
            continue
        if old_latest is None:
            old_latest = data.get("old_latest_timestamp")
        new_latest = data.get("new_latest_timestamp")
        if data.get("error") is None:
            refresh_success += 1
        else:
            refresh_failure += 1

    for path in sorted(run_dir.glob("*/signal.json")):
        data = load_json(path)
        if data is None:
            malformed_outputs += 1
            continue
        signal = data.get("signal", {}) or {}
        response = data.get("response", {}) or {}
        risk = data.get("risk", {}) or {}
        paper_state = data.get("paper_state", {}) or {}
        decision = signal.get("decision") or "UNKNOWN"
        action = response.get("action") or "UNKNOWN"
        level = risk.get("risk_level") or "UNKNOWN"
        flags = risk.get("risk_flags") or []
        signal_counts[decision] += 1
        response_counts[action] += 1
        risk_level_counts[level] += 1
        risk_flag_counts.update(flags)
        stale_data_count += int("stale_data" in flags)
        long1_count += int(signal.get("signal_name") == "Long1" or decision in {"LONG1", "LONG_SIGNAL"})
        paper_long_count += int(action == "PAPER_LONG")
        block_count += int(action == "BLOCK" or level == "BLOCK")
        latest_paper_state = paper_state

    for path in sorted(run_dir.glob("*/paper_status.json")):
        data = load_json(path)
        if data is None:
            malformed_outputs += 1
            continue
        latest_candle = data.get("data", {}) or latest_candle

    for path in sorted(run_dir.glob("*/alert_summary.json")):
        data = load_json(path)
        if data is None:
            malformed_outputs += 1
            continue
        alert_counts[data.get("overall_severity") or "UNKNOWN"] += 1

    for path in sorted(run_dir.glob("*/operator_checklist.json")):
        data = load_json(path)
        if data is None:
            malformed_outputs += 1
            continue
        checklist_counts[data.get("severity") or "UNKNOWN"] += 1

    return {
        "data_refresh_summary": {
            "attempts": refresh_attempts,
            "success_count": refresh_success,
            "failure_count": refresh_failure,
            "old_latest_timestamp": old_latest,
            "new_latest_timestamp": new_latest,
        },
        "latest_candle_summary": latest_candle,
        "signal_decision_counts": ordered_counter(signal_counts, ["WAIT", "WATCH", "LONG1", "LONG_SIGNAL", "NO_SIGNAL", "UNKNOWN", "BLOCKED"]),
        "response_action_counts": ordered_counter(response_counts, ["WAIT", "WATCH", "PAPER_LONG", "BLOCK", "EXIT_WARNING", "UNKNOWN"]),
        "risk_level_counts": ordered_counter(risk_level_counts, ["LOW", "MEDIUM", "HIGH", "BLOCK", "UNKNOWN"]),
        "risk_flag_counts": dict(sorted(risk_flag_counts.items())),
        "stale_data_count": stale_data_count,
        "long1_active_count": long1_count,
        "paper_long_count": paper_long_count,
        "block_count": block_count,
        "alert_severity_counts": ordered_counter(alert_counts, ["INFO", "WARN", "BLOCKED", "UNKNOWN"]),
        "operator_checklist_severity_counts": ordered_counter(checklist_counts, ["INFO", "WARN", "BLOCKED", "UNKNOWN"]),
        "paper_state_summary": {
            "open_position": latest_paper_state.get("open_position"),
            "position_side": latest_paper_state.get("position_side"),
            "entry_time": latest_paper_state.get("entry_time"),
            "entry_price": latest_paper_state.get("entry_price"),
        },
        "malformed_output_count": malformed_outputs,
    }


def write_summary(output_root: Path, run_dir: Path, started_at: datetime, args: argparse.Namespace, cycle_results: list[list[CommandResult]]) -> None:
    summary = build_summary(run_dir, started_at, args, cycle_results)
    write_summary_files(output_root, summary)


def write_summary_files(output_root: Path, summary: dict[str, Any]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "btc_24h_vm_observation_summary_latest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown = [
        "# BTC VM Paper Observation Summary",
        "",
        f"- Started: `{summary['started_at_utc']}`",
        f"- Completed: `{summary['completed_at_utc']}`",
        f"- Completed 24h: `{summary['completed_24h']}`",
        f"- Cycles completed: `{summary['cycles_completed']}`",
        f"- Signal decisions: `{summary['signal_decision_counts']}`",
        f"- Response actions: `{summary['response_action_counts']}`",
        f"- Risk levels: `{summary['risk_level_counts']}`",
        f"- Risk flags: `{summary['risk_flag_counts']}`",
        f"- PAPER_LONG count: `{summary['paper_long_count']}`",
        "",
        "Paper observation only. No OrderIntentWriter, adapters, private APIs, API keys, exchange orders, testnet, or live trading are enabled.",
        "",
    ]
    (output_root / "btc_24h_vm_observation_summary_latest.md").write_text("\n".join(markdown), encoding="utf-8")


def ordered_counter(counter: Counter[str], keys: list[str]) -> dict[str, int]:
    return {key: counter.get(key, 0) for key in keys}


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def resolve_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp_for_path(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def format_text(payload: dict[str, Any]) -> str:
    lines = [
        "BTC paper observation cycle",
        f"Mode: {payload['mode']}",
        f"Dry run: {payload['dry_run']}",
        f"Duration hours: {payload['duration_hours']}",
        f"Interval minutes: {payload['interval_minutes']}",
        "Safety:",
    ]
    lines.extend(f"- {key}: {value}" for key, value in payload["safety"].items())
    lines.append("Safe commands:")
    lines.extend("- " + " ".join(command) for command in payload["safe_commands"])
    if "cycles_completed" in payload:
        lines.append(f"Cycles completed: {payload['cycles_completed']}")
    if "summary" in payload:
        lines.append(payload["summary"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = build_parser().parse_args()
    payload = run_observation(args)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
