from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HEARTBEAT_PATH = PROJECT_ROOT / "logs" / "heartbeat.csv"
TRADES_PATH = PROJECT_ROOT / "logs" / "trades.csv"
PAPER_STATE_PATH = PROJECT_ROOT / "data" / "paper_state.json"


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    seconds = max(int(seconds), 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h {minutes}m {secs}s"


def numeric_values(rows: list[dict[str, str]], field: str) -> list[int]:
    values = []
    for row in rows:
        raw = row.get(field)
        if raw in {None, ""}:
            continue
        try:
            values.append(int(float(raw)))
        except ValueError:
            continue
    return values


def value_changes(rows: list[dict[str, str]], field: str) -> tuple[list[str], int]:
    values = [row.get(field, "") for row in rows if row.get(field, "") != ""]
    unique_values = []
    transitions = 0
    previous = None
    for value in values:
        if value not in unique_values:
            unique_values.append(value)
        if previous is not None and value != previous:
            transitions += 1
        previous = value
    return unique_values, transitions


def loop_count_summary(rows: list[dict[str, str]]) -> str:
    if not rows or "loop_count" not in rows[0]:
        return "loop_count column missing"

    previous_by_identity: dict[tuple[str, str], int] = {}
    decreases = []
    missing = 0

    for index, row in enumerate(rows, start=1):
        raw_loop = row.get("loop_count", "")
        if raw_loop == "":
            missing += 1
            continue
        try:
            loop_count = int(float(raw_loop))
        except ValueError:
            missing += 1
            continue

        identity = (row.get("boot_id", ""), row.get("process_id", ""))
        previous = previous_by_identity.get(identity)
        if previous is not None and loop_count < previous:
            decreases.append((index, previous, loop_count, identity))
        previous_by_identity[identity] = loop_count

    if decreases:
        return f"FAILED: {len(decreases)} decrease(s), first={decreases[0]}"
    if missing:
        return f"OK for parsed rows; {missing} missing/unparseable loop_count value(s)"
    return "OK: monotonic within each process_id/boot_id"


def heartbeat_gap_summary(rows: list[dict[str, str]]) -> str:
    timestamps = [parse_timestamp(row.get("timestamp")) for row in rows]
    timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
    if len(timestamps) < 2:
        return "not enough heartbeat rows"

    gaps = [
        (current - previous).total_seconds()
        for previous, current in zip(timestamps, timestamps[1:])
    ]
    sorted_gaps = sorted(gaps)
    median_gap = sorted_gaps[len(sorted_gaps) // 2]
    large_gap_threshold = max(120.0, median_gap * 3)
    large_gaps = [gap for gap in gaps if gap > large_gap_threshold]
    largest_gap = max(gaps)

    return (
        f"{len(large_gaps)} large gap(s); "
        f"largest={format_duration(largest_gap)}, "
        f"median={format_duration(median_gap)}, "
        f"threshold={format_duration(large_gap_threshold)}"
    )


def candle_summary(rows: list[dict[str, str]]) -> str:
    if not rows or "candle_timestamp" not in rows[0]:
        return "candle_timestamp column missing"

    candles = [row.get("candle_timestamp", "") for row in rows]
    candles = [candle for candle in candles if candle]
    if not candles:
        return "no candle timestamps recorded"

    unique_candles = list(dict.fromkeys(candles))
    updates = sum(1 for previous, current in zip(candles, candles[1:]) if current != previous)
    counts = Counter(candles)
    most_common_candle, most_common_count = counts.most_common(1)[0]
    return (
        f"unique={len(unique_candles)}, updates={updates}, "
        f"first={unique_candles[0]}, last={unique_candles[-1]}, "
        f"most_common={most_common_candle} ({most_common_count} heartbeat row(s))"
    )


def dry_run_summary(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "no heartbeat rows"
    values = Counter(row.get("dry_run", "") for row in rows)
    unsafe = {value: count for value, count in values.items() if value not in {"1", "true", "True"}}
    if unsafe:
        return f"FAILED: non-dry-run heartbeat values={unsafe}"
    return f"OK: all {len(rows)} heartbeat row(s) are dry_run"


def trade_summary(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "no trades logged"

    action_counts = Counter(row.get("action", "") for row in rows)
    side_counts = Counter(row.get("side", "") for row in rows)
    dry_run_values = Counter(row.get("dry_run", "") for row in rows)
    return (
        f"{len(rows)} trade row(s); "
        f"actions={dict(action_counts)}, sides={dict(side_counts)}, dry_run={dict(dry_run_values)}"
    )


def paper_state_summary(state: dict[str, Any]) -> str:
    if not state:
        return "paper_state.json missing or empty"

    keys = [
        "current_simulated_position",
        "entry_price",
        "size",
        "stop_price",
        "realized_pnl",
        "unrealized_pnl",
        "number_of_trades",
        "last_signal",
        "last_update_timestamp",
        "LAST_PROCESSED_CANDLE_TIMESTAMP",
        "daily_entries_blocked",
        "monthly_entries_blocked",
        "last_error",
    ]
    return "\n".join(f"  {key}: {state.get(key)}" for key in keys)


def main() -> None:
    heartbeat_rows = read_csv_rows(HEARTBEAT_PATH)
    trade_rows = read_csv_rows(TRADES_PATH)
    paper_state = read_json(PAPER_STATE_PATH)

    heartbeat_times = [parse_timestamp(row.get("timestamp")) for row in heartbeat_rows]
    heartbeat_times = [value for value in heartbeat_times if value is not None]
    runtime_start = heartbeat_times[0] if heartbeat_times else None
    runtime_end = heartbeat_times[-1] if heartbeat_times else None
    uptime_seconds = (
        (runtime_end - runtime_start).total_seconds()
        if runtime_start is not None and runtime_end is not None
        else None
    )

    process_ids, process_transitions = value_changes(heartbeat_rows, "process_id")
    boot_ids, boot_transitions = value_changes(heartbeat_rows, "boot_id")
    error_counts = numeric_values(heartbeat_rows, "error_count")

    print("Runtime Log Analysis")
    print(f"heartbeat_path: {HEARTBEAT_PATH}")
    print(f"trades_path: {TRADES_PATH}")
    print(f"paper_state_path: {PAPER_STATE_PATH}")
    print()
    print(f"1. total heartbeat rows: {len(heartbeat_rows)}")
    print(f"2. observed runtime start/end: {runtime_start} -> {runtime_end}")
    print(f"3. estimated uptime duration: {format_duration(uptime_seconds)}")
    print(
        "4. process_id changes: "
        f"unique={len(process_ids)}, transitions={process_transitions}, values={process_ids}"
    )
    print(
        "5. boot_id changes: "
        f"unique={len(boot_ids)}, transitions={boot_transitions}, values={boot_ids}"
    )
    print(f"6. loop_count monotonicity check: {loop_count_summary(heartbeat_rows)}")
    print(
        "7. error_count summary: "
        f"max={max(error_counts) if error_counts else 0}, "
        f"last={error_counts[-1] if error_counts else 0}, "
        f"nonzero_rows={sum(1 for value in error_counts if value > 0)}"
    )
    print(f"8. candle_timestamp update summary: {candle_summary(heartbeat_rows)}")
    print(f"9. dry_run consistency check: {dry_run_summary(heartbeat_rows)}")
    print(f"10. whether any trades were logged: {trade_summary(trade_rows)}")
    print(f"11. whether there are large heartbeat gaps: {heartbeat_gap_summary(heartbeat_rows)}")
    print("12. final paper_state summary:")
    print(paper_state_summary(paper_state))


if __name__ == "__main__":
    main()
