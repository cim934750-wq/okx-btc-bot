#!/usr/bin/env python3
"""CP1 4h BTC public-trade reconstruction pilot round 1.

Research-only data-engineering audit. The script fetches only the approved CP1
BTC-USDT-SWAP OKX public history-trades pages when no CP1 raw archive exists.
If an existing CP1 raw archive is present, it processes that archive without
performing additional network requests.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

BASE_URL = "https://www.okx.com"
ENDPOINT = "/api/v5/market/history-trades"
PREFIX = "cp1_4h_btc_public_trade_reconstruction_pilot_round1"
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "research_output"
RAW_DIR = OUT_DIR / f"{PREFIX}_raw"
CHECKPOINT_ID = "CP1"
MARKET = "BTCUSDT"
INST_ID = "BTC-USDT-SWAP"
INST_TYPE = "SWAP"
REQUIRED_FIELDS = ["instId", "tradeId", "ts", "px", "sz", "side"]
MAX_REQUESTS = 2500
MAX_RUNTIME_SECONDS = 45 * 60
MAX_RAW_STORAGE_MB = 500
LIMIT = 100
MAX_RETRIES = 3
REQUEST_PAUSE_SECONDS = 0.22
SAFETY_LAG_MINUTES = 15

try:
    import certifi  # type: ignore
except Exception:  # pragma: no cover
    certifi = None
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()


@dataclass
class PageData:
    page_seq: int
    path: Path
    raw_bytes: bytes
    payload: dict[str, Any]
    rows: list[dict[str, Any]]
    sha256: str
    fetch_timestamp_utc: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def parse_ms(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def iso_ms(value: Any) -> str:
    ts = parse_ms(value)
    if ts is None:
        return ""
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()


def parse_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def fmt_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cursor_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def select_completed_4h_interval(reference: datetime) -> tuple[datetime, datetime]:
    boundary_hour = (reference.hour // 4) * 4
    end = reference.replace(hour=boundary_hour, minute=0, second=0, microsecond=0)
    if reference - end < timedelta(minutes=SAFETY_LAG_MINUTES):
        end -= timedelta(hours=4)
    return end - timedelta(hours=4), end


def window_label(start: datetime, end: datetime) -> str:
    return f"{iso_z(start).replace('-', '').replace(':', '')}_{iso_z(end).replace('-', '').replace(':', '')}"


def parse_window_label(label: str) -> tuple[datetime, datetime]:
    m = re.fullmatch(r"(\d{8}T\d{6}Z)_(\d{8}T\d{6}Z)", label)
    if not m:
        raise ValueError(f"Unexpected CP1 raw window label: {label}")
    start = datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    end = datetime.strptime(m.group(2), "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return start, end


def raw_page_path(page_seq: int, cursor_after: int, start: datetime, end: datetime) -> Path:
    d = RAW_DIR / CHECKPOINT_ID / INST_ID / window_label(start, end)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"page_{page_seq:06d}_{cursor_hash(str(cursor_after))}.json"


def existing_window() -> tuple[Path, datetime, datetime] | None:
    root = RAW_DIR / CHECKPOINT_ID / INST_ID
    if not root.exists():
        return None
    windows = sorted([p for p in root.iterdir() if p.is_dir()])
    if not windows:
        return None
    start, end = parse_window_label(windows[-1].name)
    return windows[-1], start, end


def fetch_page(page_seq: int, cursor_after: int, start: datetime, end: datetime) -> tuple[Path, bool, int, str]:
    params = {"instId": INST_ID, "type": "2", "after": str(cursor_after), "limit": str(LIMIT)}
    url = f"{BASE_URL}{ENDPOINT}?{urllib.parse.urlencode(params)}"
    path = raw_page_path(page_seq, cursor_after, start, end)
    raw = b""
    status = "not_requested"
    retries = 0
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "okx-btc-bot-research-cp1-audit/1.0"})
            with urllib.request.urlopen(req, timeout=30, context=SSL_CONTEXT) as response:
                raw = response.read()
                status = f"http_{response.status}"
                break
        except urllib.error.HTTPError as exc:
            raw = exc.read() if exc.fp else b""
            status = f"http_error_{exc.code}"
            if attempt >= MAX_RETRIES:
                break
            retries += 1
            time.sleep(min(2 ** attempt, 8))
        except Exception as exc:
            raw = json.dumps({"error": repr(exc), "url": url}).encode("utf-8")
            status = "request_error"
            if attempt >= MAX_RETRIES:
                break
            retries += 1
            time.sleep(min(2 ** attempt, 8))
    path.write_bytes(raw)
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
        ok = isinstance(payload, dict) and str(payload.get("code")) == "0" and status.startswith("http_200")
    except Exception:
        ok = False
    return path, ok, retries, status


def fetch_cp1_archive(start: datetime, end: datetime) -> str:
    cursor_after = int(end.timestamp() * 1000)
    stop_reason = ""
    started = time.monotonic()
    for page_seq in range(1, MAX_REQUESTS + 1):
        if time.monotonic() - started > MAX_RUNTIME_SECONDS:
            return "runtime_cap_reached_before_bucket_start"
        path, ok, _, status = fetch_page(page_seq, cursor_after, start, end)
        if not ok:
            return f"request_failure_{status}"
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        ts_values = [v for v in (parse_ms(r.get("ts")) for r in rows if isinstance(r, dict)) if v is not None]
        if not ts_values:
            return "empty_or_unparseable_page"
        earliest = min(ts_values)
        if earliest <= int(start.timestamp() * 1000):
            return "covered_to_or_before_bucket_start"
        cursor_after = earliest
        time.sleep(REQUEST_PAUSE_SECONDS)
    return "request_cap_reached_before_bucket_start"


def load_pages(window_dir: Path) -> list[PageData]:
    pages: list[PageData] = []
    for path in sorted(window_dir.glob("page_*.json")):
        m = re.search(r"page_(\d+)_", path.name)
        page_seq = int(m.group(1)) if m else len(pages) + 1
        raw = path.read_bytes()
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            payload = {"decode_error": True, "data": []}
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        clean_rows = [r for r in rows if isinstance(r, dict)]
        fetch_ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        pages.append(PageData(page_seq, path, raw, payload, clean_rows, sha256_bytes(raw), fetch_ts))
    return pages


def local_side_semantics() -> tuple[bool, str]:
    path = OUT_DIR / "minimal_public_trade_reconstruction_audit_round1_side_semantics.csv"
    if not path.exists():
        return False, "prior side semantics artifact missing; no live docs fetched"
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            meaning = row.get("documented_meaning", "")
            proof = row.get("taker_aggressor_side_proven", "")
            if "taker" in meaning.lower() and "yes" in proof:
                return True, f"Prior committed artifact records OKX docs meaning as '{meaning}'. Reference/note: {row.get('proof_reference_or_note','')}."
    return False, "prior artifact did not provide taker/aggressor proof; no live docs fetched"


def main() -> None:
    started = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    existing = existing_window()
    if existing:
        window_dir, start, end = existing
        fetch_mode = "processed_existing_raw_archive_without_additional_fetch"
        fetch_stop_reason = "existing_raw_archive_used"
    else:
        start, end = select_completed_4h_interval(now_utc())
        fetch_stop_reason = fetch_cp1_archive(start, end)
        window_dir = RAW_DIR / CHECKPOINT_ID / INST_ID / window_label(start, end)
        fetch_mode = "fetched_cp1_public_history_trades"

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    pages = load_pages(window_dir)
    page_count = len(pages)
    raw_bytes_total = sum(len(p.raw_bytes) for p in pages)
    mtime_values = [p.path.stat().st_mtime for p in pages]
    archive_runtime_seconds = (max(mtime_values) - min(mtime_values)) if len(mtime_values) > 1 else 0.0

    all_rows: list[dict[str, Any]] = []
    fetch_log: list[dict[str, Any]] = []
    cursor_after = end_ms
    request_failures = 0
    for page in pages:
        params = {"instId": INST_ID, "type": "2", "after": str(cursor_after), "limit": str(LIMIT)}
        payload_code = page.payload.get("code", "") if isinstance(page.payload, dict) else ""
        status = f"raw_archive_code_{payload_code}" if payload_code != "" else "raw_archive_unknown_code"
        ts_values = [v for v in (parse_ms(r.get("ts")) for r in page.rows) if v is not None]
        if str(payload_code) != "0":
            request_failures += 1
        rel_path = str(page.path.relative_to(REPO_ROOT))
        for row in page.rows:
            row["_page_seq"] = page.page_seq
            row["_raw_path"] = rel_path
        all_rows.extend(page.rows)
        fetch_log.append({
            "request_id": f"cp1_history_page_{page.page_seq:06d}",
            "endpoint": ENDPOINT,
            "inst_id": INST_ID,
            "request_params": json.dumps(params, sort_keys=True),
            "fetch_timestamp_utc": page.fetch_timestamp_utc,
            "response_status": status,
            "rows_returned": len(page.rows),
            "earliest_ts": iso_ms(min(ts_values)) if ts_values else "",
            "latest_ts": iso_ms(max(ts_values)) if ts_values else "",
            "raw_path": rel_path,
            "sha256": page.sha256,
            "retry_count": 0,
            "rate_limit_note": "unknown_from_existing_archive" if fetch_mode.startswith("processed") else "none",
            "notes": f"{fetch_mode}; request_params reconstructed from CP1 cursor sequence; no private/account/order data",
        })
        if ts_values:
            cursor_after = min(ts_values)

    rows_in_bucket = [r for r in all_rows if r.get("instId") == INST_ID and parse_ms(r.get("ts")) is not None and start_ms <= int(r["ts"]) < end_ms]
    pass_required_fields = bool(rows_in_bucket)
    field_rows = []
    for field in REQUIRED_FIELDS:
        present_count = sum(1 for r in rows_in_bucket if r.get(field) not in (None, ""))
        present = bool(rows_in_bucket) and present_count == len(rows_in_bucket)
        pass_required_fields = pass_required_fields and present
        sample_value = next((str(r.get(field)) for r in rows_in_bucket if r.get(field) not in (None, "")), "")
        field_rows.append({"inst_id": INST_ID, "field_name": field, "present": str(present).lower(), "sample_value": sample_value, "required_for_reconstruction": "yes", "missing_impact": "hard_stop_if_missing_in_any_bucket_row", "notes": f"present_count={present_count}; bucket_row_count={len(rows_in_bucket)}"})

    side_proven, side_note = local_side_semantics()

    seen: dict[tuple[str, str], dict[str, Any]] = {}
    deduped: list[dict[str, Any]] = []
    duplicate_count = 0
    conflicting_duplicate_count = 0
    conflicts: list[dict[str, Any]] = []
    for row in rows_in_bucket:
        key = (str(row.get("instId", "")), str(row.get("tradeId", "")))
        if not key[1]:
            key = (str(row.get("instId", "")), "fallback:" + "|".join(str(row.get(k, "")) for k in ["ts", "px", "sz", "side"]))
        if key not in seen:
            seen[key] = row
            deduped.append(row)
            continue
        duplicate_count += 1
        prior = seen[key]
        if any(str(prior.get(f, "")) != str(row.get(f, "")) for f in ["ts", "px", "sz", "side"]):
            conflicting_duplicate_count += 1
            conflicts.append(row)
    quarantine_path = ""
    if conflicts:
        q = OUT_DIR / f"{PREFIX}_duplicate_conflicts_quarantine.json"
        q.write_text(json.dumps(conflicts, indent=2, sort_keys=True), encoding="utf-8")
        quarantine_path = str(q.relative_to(REPO_ROOT))
    duplicate_rate = Decimal(duplicate_count) / Decimal(len(rows_in_bucket)) if rows_in_bucket else Decimal("0")

    page_summaries = []
    for page in pages:
        ts_values = [v for v in (parse_ms(r.get("ts")) for r in page.rows) if v is not None]
        page_summaries.append({"seq": page.page_seq, "earliest": min(ts_values) if ts_values else None, "latest": max(ts_values) if ts_values else None, "rows": len(page.rows)})
    visible_gap_count = 0
    pagination_notes = []
    for prev, cur in zip(page_summaries, page_summaries[1:]):
        if prev["earliest"] is None or cur["latest"] is None:
            visible_gap_count += 1
            pagination_notes.append(f"missing timestamp diagnostics page {prev['seq']} to {cur['seq']}")
        elif cur["latest"] > prev["earliest"]:
            visible_gap_count += 1
            pagination_notes.append(f"unexpected timestamp order page {prev['seq']} to {cur['seq']}")
    ts_bucket = [v for v in (parse_ms(r.get("ts")) for r in rows_in_bucket) if v is not None]
    earliest_bucket_ts = min(ts_bucket) if ts_bucket else None
    latest_bucket_ts = max(ts_bucket) if ts_bucket else None
    fetched_before_start = bool(page_summaries) and page_summaries[-1]["earliest"] is not None and int(page_summaries[-1]["earliest"]) <= start_ms
    request_cap_reached_before_start = page_count >= MAX_REQUESTS and not fetched_before_start
    if request_failures or visible_gap_count or request_cap_reached_before_start:
        unresolved_gap_risk = "true"
    else:
        unresolved_gap_risk = "false"

    processing_runtime_seconds = time.monotonic() - started
    runtime_seconds = archive_runtime_seconds + processing_runtime_seconds
    raw_storage_mb = raw_bytes_total / (1024 * 1024)
    processed_storage_bytes = sum(p.stat().st_size for p in OUT_DIR.glob(f"{PREFIX}_*") if p.is_file())
    pass_duplicate_check = conflicting_duplicate_count == 0 and duplicate_rate <= Decimal("0.01")
    pass_pagination_check = unresolved_gap_risk == "false"
    pass_resource_budget = page_count <= MAX_REQUESTS and runtime_seconds <= MAX_RUNTIME_SECONDS and raw_storage_mb <= MAX_RAW_STORAGE_MB
    bucket_complete = all([pass_required_fields, side_proven, pass_duplicate_check, pass_pagination_check, pass_resource_budget, fetched_before_start, bool(rows_in_bucket)])

    incomplete_reasons = []
    if not rows_in_bucket:
        incomplete_reasons.append("no_rows_inside_bucket")
    if request_cap_reached_before_start:
        incomplete_reasons.append("request_cap_reached_before_bucket_start")
    if not fetched_before_start:
        incomplete_reasons.append("did_not_fetch_to_bucket_start")
    if not pass_required_fields:
        incomplete_reasons.append("required_field_coverage_not_100pct")
    if not side_proven:
        incomplete_reasons.append("side_semantics_unproven")
    if conflicting_duplicate_count:
        incomplete_reasons.append("conflicting_duplicate_count_gt_0")
    if duplicate_rate > Decimal("0.01"):
        incomplete_reasons.append("benign_duplicate_rate_gt_1pct")
    if not pass_pagination_check:
        incomplete_reasons.append("unresolved_pagination_gap_risk")
    if not pass_resource_budget:
        incomplete_reasons.append("resource_budget_failed")

    buy_volume = Decimal("0")
    sell_volume = Decimal("0")
    for row in deduped:
        side = str(row.get("side", "")).lower()
        size = parse_decimal(row.get("sz"))
        if side == "buy":
            buy_volume += size
        elif side == "sell":
            sell_volume += size
    total_volume = buy_volume + sell_volume
    buy_ratio = buy_volume / total_volume if total_volume else Decimal("0")
    sell_ratio = sell_volume / total_volume if total_volume else Decimal("0")
    imbalance = (buy_volume - sell_volume) / total_volume if total_volume else Decimal("0")
    delta = buy_volume - sell_volume

    if bucket_complete:
        decision = "cp1_pass_go_to_cp2_plan"
        allowed_next_step = "create_CP2_1day_execution_prompt_only"
        forbidden_next_step = "do_not_execute_CP2_automatically; no_strategy_validation; no_all_market_fetch"
    elif not side_proven:
        decision = "cp1_fail_side_semantics"
        allowed_next_step = "stop_or_produce_side_semantics_evidence_plan"
        forbidden_next_step = "do_not_compute_exact_taker_flow_claims"
    elif conflicting_duplicate_count:
        decision = "cp1_fail_duplicate_conflict"
        allowed_next_step = "stop_and_inspect_quarantined_duplicates"
        forbidden_next_step = "do_not_drop_conflicting_duplicates_silently"
    elif not pass_pagination_check and not request_cap_reached_before_start:
        decision = "cp1_fail_pagination_gap"
        allowed_next_step = "redesign_pagination_probe_or_external_data_audit"
        forbidden_next_step = "do_not_advance_to_CP2"
    elif not bucket_complete:
        decision = "cp1_fail_incomplete_bucket"
        allowed_next_step = "stop_or_redesign_reconstruction_method"
        forbidden_next_step = "do_not_advance_to_CP2"
    elif not pass_resource_budget:
        decision = "cp1_fail_rate_limit_runtime_storage"
        allowed_next_step = "stop_or_reduce_scope"
        forbidden_next_step = "do_not_continue_fetching"
    else:
        decision = "cp1_inconclusive_needs_smaller_probe"
        allowed_next_step = "smaller_endpoint_pagination_probe"
        forbidden_next_step = "do_not_advance_to_CP2"

    write_csv(OUT_DIR / f"{PREFIX}_fetch_log.csv", ["request_id", "endpoint", "inst_id", "request_params", "fetch_timestamp_utc", "response_status", "rows_returned", "earliest_ts", "latest_ts", "raw_path", "sha256", "retry_count", "rate_limit_note", "notes"], fetch_log)
    write_csv(OUT_DIR / f"{PREFIX}_market_mapping.csv", ["market", "okx_inst_id", "instrument_type", "mapping_source", "mapping_confidence", "notes"], [{"market": MARKET, "okx_inst_id": INST_ID, "instrument_type": INST_TYPE, "mapping_source": "minimal_public_trade_reconstruction_audit_round1 and bounded_30d_public_trade_reconstruction_audit_plan_round1", "mapping_confidence": "high", "notes": "CP1 scope is BTC only; DOGE DOT and all-19 markets were not fetched"}])
    write_csv(OUT_DIR / f"{PREFIX}_field_coverage.csv", ["inst_id", "field_name", "present", "sample_value", "required_for_reconstruction", "missing_impact", "notes"], field_rows)
    write_csv(OUT_DIR / f"{PREFIX}_side_semantics.csv", ["source", "field_name", "documented_meaning", "taker_aggressor_side_proven", "proof_reference_or_note", "decision_impact", "notes"], [{"source": "prior committed minimal audit local artifact", "field_name": "side", "documented_meaning": "Trade side of taker for OKX public trades endpoints", "taker_aggressor_side_proven": "yes_documented_with_caveat" if side_proven else "no_unproven", "proof_reference_or_note": side_note, "decision_impact": "allows_CP1_sample_taker_flow_features_with_documentation_caveat" if side_proven else "blocks_exact_taker_flow_reconstruction", "notes": "No live documentation fetch was performed in CP1; this relies on committed local audit evidence only."}])
    write_csv(OUT_DIR / f"{PREFIX}_dedup_check.csv", ["inst_id", "rows_raw", "rows_after_dedup", "duplicate_count", "duplicate_rate", "conflicting_duplicate_count", "dedup_key", "quarantine_path", "notes"], [{"inst_id": INST_ID, "rows_raw": len(rows_in_bucket), "rows_after_dedup": len(deduped), "duplicate_count": duplicate_count, "duplicate_rate": fmt_decimal(duplicate_rate), "conflicting_duplicate_count": conflicting_duplicate_count, "dedup_key": "primary=instId+tradeId; fallback=instId+ts+px+sz+side if tradeId missing", "quarantine_path": quarantine_path, "notes": "Conflicting duplicates are a hard stop; benign duplicate rate must be <=1.0%."}])
    write_csv(OUT_DIR / f"{PREFIX}_pagination_check.csv", ["inst_id", "page_count", "request_count", "earliest_ts", "latest_ts", "timestamp_order", "overlap_count", "visible_gap_count", "unresolved_gap_risk", "notes"], [{"inst_id": INST_ID, "page_count": page_count, "request_count": page_count, "earliest_ts": iso_ms(earliest_bucket_ts), "latest_ts": iso_ms(latest_bucket_ts), "timestamp_order": "descending_by_page", "overlap_count": duplicate_count, "visible_gap_count": visible_gap_count, "unresolved_gap_risk": unresolved_gap_risk, "notes": "; ".join(pagination_notes) if pagination_notes else f"fetch_mode={fetch_mode}; fetch_stop_reason={fetch_stop_reason}; request_cap_reached_before_start={request_cap_reached_before_start}"}])
    write_csv(OUT_DIR / f"{PREFIX}_bucket_completeness.csv", ["inst_id", "bucket_start_utc", "bucket_end_utc", "requested_interval_complete", "earliest_trade_ts", "latest_trade_ts", "bucket_complete", "incomplete_reason", "gap_flag", "notes"], [{"inst_id": INST_ID, "bucket_start_utc": iso_z(start), "bucket_end_utc": iso_z(end), "requested_interval_complete": str(fetched_before_start and pass_pagination_check).lower(), "earliest_trade_ts": iso_ms(earliest_bucket_ts), "latest_trade_ts": iso_ms(latest_bucket_ts), "bucket_complete": str(bucket_complete).lower(), "incomplete_reason": ";".join(incomplete_reasons), "gap_flag": str(unresolved_gap_risk == "true").lower(), "notes": "bucket_complete=True only if all CP1 stop/go checks pass; interval is half-open [start,end)."}])
    write_csv(OUT_DIR / f"{PREFIX}_4h_bucket_features.csv", ["inst_id", "bucket_start_utc", "bucket_end_utc", "bucket_complete", "trade_count", "unique_trade_count", "duplicate_count", "taker_buy_volume", "taker_sell_volume", "total_taker_volume", "taker_buy_ratio", "taker_sell_ratio", "taker_imbalance", "taker_delta", "caveat", "notes"], [{"inst_id": INST_ID, "bucket_start_utc": iso_z(start), "bucket_end_utc": iso_z(end), "bucket_complete": str(bucket_complete).lower(), "trade_count": len(rows_in_bucket), "unique_trade_count": len(deduped), "duplicate_count": duplicate_count, "taker_buy_volume": fmt_decimal(buy_volume), "taker_sell_volume": fmt_decimal(sell_volume), "total_taker_volume": fmt_decimal(total_volume), "taker_buy_ratio": fmt_decimal(buy_ratio), "taker_sell_ratio": fmt_decimal(sell_ratio), "taker_imbalance": fmt_decimal(imbalance), "taker_delta": fmt_decimal(delta), "caveat": "valid_for_CP1_completed_bucket_only" if bucket_complete else "diagnostic_only_bucket_not_complete_or_failed_gate", "notes": "Volumes are summed from OKX public trade sz by documented taker side; no notional conversion audited here."}])

    sample = sorted(deduped, key=lambda r: int(r.get("ts", "0")))
    if len(sample) > 40:
        sample = sample[:20] + sample[-20:]
    write_csv(OUT_DIR / f"{PREFIX}_sample_trades.csv", ["row_seq", "inst_id", "trade_id", "ts", "ts_utc", "px", "sz", "side", "page_seq", "raw_path"], [{"row_seq": i, "inst_id": r.get("instId", ""), "trade_id": r.get("tradeId", ""), "ts": r.get("ts", ""), "ts_utc": iso_ms(r.get("ts")), "px": r.get("px", ""), "sz": r.get("sz", ""), "side": r.get("side", ""), "page_seq": r.get("_page_seq", ""), "raw_path": r.get("_raw_path", "")} for i, r in enumerate(sample, start=1)])
    write_csv(OUT_DIR / f"{PREFIX}_storage_runtime.csv", ["checkpoint_id", "inst_id", "request_count", "rows_raw", "rows_after_dedup", "raw_storage_mb", "processed_storage_mb", "runtime_seconds", "within_request_cap", "within_runtime_cap", "within_storage_cap", "notes"], [{"checkpoint_id": CHECKPOINT_ID, "inst_id": INST_ID, "request_count": page_count, "rows_raw": len(rows_in_bucket), "rows_after_dedup": len(deduped), "raw_storage_mb": f"{raw_storage_mb:.6f}", "processed_storage_mb": f"{processed_storage_bytes / (1024 * 1024):.6f}", "runtime_seconds": f"{runtime_seconds:.3f}", "within_request_cap": str(page_count <= MAX_REQUESTS).lower(), "within_runtime_cap": str(runtime_seconds <= MAX_RUNTIME_SECONDS).lower(), "within_storage_cap": str(raw_storage_mb <= MAX_RAW_STORAGE_MB).lower(), "notes": f"CP1 caps: 2500 requests, 45 minutes runtime, 500 MB raw archive. Runtime uses raw archive file mtime span ({archive_runtime_seconds:.3f}s) plus current processing time ({processing_runtime_seconds:.3f}s) because initial post-processing was interrupted after raw archive completion."}])
    write_csv(OUT_DIR / f"{PREFIX}_stop_go_decision.csv", ["checkpoint_id", "decision", "pass_required_fields", "pass_side_semantics", "pass_duplicate_check", "pass_bucket_completeness", "pass_pagination_check", "pass_resource_budget", "allowed_next_step", "forbidden_next_step", "notes"], [{"checkpoint_id": CHECKPOINT_ID, "decision": decision, "pass_required_fields": str(pass_required_fields).lower(), "pass_side_semantics": str(side_proven).lower(), "pass_duplicate_check": str(pass_duplicate_check).lower(), "pass_bucket_completeness": str(bucket_complete).lower(), "pass_pagination_check": str(pass_pagination_check).lower(), "pass_resource_budget": str(pass_resource_budget).lower(), "allowed_next_step": allowed_next_step, "forbidden_next_step": forbidden_next_step, "notes": ";".join(incomplete_reasons) if incomplete_reasons else "CP1 passed all stop/go gates; CP2 is not executed automatically."}])

    note = f"""# CP1 4h BTC Public-Trade Reconstruction Pilot Round 1

## Scope
- Checkpoint: CP1 only.
- Instrument: BTCUSDT mapped to `BTC-USDT-SWAP`.
- Endpoint used: OKX public REST `{ENDPOINT}` only.
- Selected interval: `{iso_z(start)}` to `{iso_z(end)}` UTC, half-open `[start,end)`.
- Public trades fetched only for BTC-USDT-SWAP. DOGE, DOT, and all-19 markets were not fetched.

## Result
- Decision: `{decision}`.
- Pages/requests archived: {page_count} of max {MAX_REQUESTS}.
- Raw archive MB: {raw_storage_mb:.6f} of max {MAX_RAW_STORAGE_MB}.
- Bucket complete: {bucket_complete}.
- Rows inside bucket: {len(rows_in_bucket)} raw, {len(deduped)} deduplicated.
- Earliest bucket trade reached: {iso_ms(earliest_bucket_ts)}.
- Latest bucket trade reached: {iso_ms(latest_bucket_ts)}.

## Interpretation
CP1 did not prove 30-day feasibility. It only tests whether one completed BTC 4h bucket can be reconstructed under the CP1 cap. If the decision is not `cp1_pass_go_to_cp2_plan`, CP2 must not be executed automatically.

Side semantics rely on the committed prior minimal audit artifact, which recorded OKX documentation for `side` as the trade side of taker. No live documentation fetch was performed during CP1.

## Next Step
Allowed next step: {allowed_next_step}.
Forbidden next step: {forbidden_next_step}.
"""
    (OUT_DIR / f"{PREFIX}_note.md").write_text(note, encoding="utf-8")
    (OUT_DIR / f"{PREFIX}_limitations.md").write_text(f"""# CP1 4h BTC Public-Trade Reconstruction Pilot Limitations

- CP1 covers exactly one completed UTC 4h interval for BTC-USDT-SWAP only.
- CP1 does not prove 1-day, 7-day, 30-day, DOGE, DOT, or all-19 feasibility.
- CP1 does not validate any trading strategy or active edge.
- Side semantics are accepted from previously committed local audit evidence, not from independent order-book replay.
- Volume fields use OKX trade `sz` units; notional reconstruction and contract metadata were not audited in CP1.
- Any incomplete bucket, unresolved pagination risk, duplicate conflict, side-semantics uncertainty, or resource-budget breach blocks CP2 advancement.
""", encoding="utf-8")
    (OUT_DIR / f"{PREFIX}_handoff.md").write_text(f"""# CP1 4h BTC Public-Trade Reconstruction Pilot Round 1 Handoff

- Scope: BTC-USDT-SWAP only, one completed UTC 4h interval, OKX public REST history-trades only.
- Selected interval: {iso_z(start)} to {iso_z(end)} UTC.
- Pages/requests archived: {page_count}; raw archive MB: {raw_storage_mb:.6f}; estimated total runtime seconds: {runtime_seconds:.3f}.
- Required fields pass: {pass_required_fields}.
- Side semantics pass: {side_proven}, using committed local prior audit evidence only.
- Duplicate check pass: {pass_duplicate_check}; conflicts: {conflicting_duplicate_count}; duplicate rate: {fmt_decimal(duplicate_rate)}.
- Pagination check pass: {pass_pagination_check}; unresolved gap risk: {unresolved_gap_risk}.
- Bucket complete: {bucket_complete}.
- Decision: {decision}.
- Allowed next step: {allowed_next_step}.
- Implementation readiness: none; not dry-run-ready; not live-ready.
""", encoding="utf-8")

    print(json.dumps({"decision": decision, "bucket_start_utc": iso_z(start), "bucket_end_utc": iso_z(end), "page_count": page_count, "rows_in_bucket": len(rows_in_bucket), "rows_after_dedup": len(deduped), "bucket_complete": bucket_complete, "raw_storage_mb": round(raw_storage_mb, 6), "estimated_total_runtime_seconds": round(runtime_seconds, 3),
        "processing_runtime_seconds": round(processing_runtime_seconds, 3),
        "archive_runtime_seconds": round(archive_runtime_seconds, 3), "fetch_mode": fetch_mode}, indent=2))


if __name__ == "__main__":
    main()
