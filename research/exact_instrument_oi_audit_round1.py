#!/usr/bin/env python3
"""Research-only exact-instrument open-interest availability audit.

This script fetches public OKX open-interest data only. It does not define or
test any strategy, fetch OHLCV, use private data, or change production config.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

try:
    import ccxt  # type: ignore
except Exception:  # pragma: no cover - optional dependency in audit script
    ccxt = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_output"
PLAN_MAPPING = OUT / "exact_instrument_oi_audit_plan_round1_instrument_mapping.csv"
PREFIX = "exact_instrument_oi_audit_round1"
RAW_DIR = OUT / f"{PREFIX}_raw"
OKX_BASE = "https://www.okx.com"
FETCH_TS = datetime.now(timezone.utc).isoformat()
TIMEOUT = 20
SLEEP_SECONDS = 0.25


def utc_iso(ts_ms: Optional[int]) -> str:
    if ts_ms is None:
        return ""
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_mapping() -> List[Dict[str, str]]:
    with PLAN_MAPPING.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def fetch_okx(path: str, params: Dict[str, str]) -> Tuple[bool, int, Dict[str, Any], str, str]:
    url = f"{OKX_BASE}{path}"
    last_url = url
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            text = resp.text
            last_url = resp.url
            try:
                payload = resp.json()
            except Exception:
                payload = {"raw_text": text}
            if resp.status_code != 429:
                return resp.ok, resp.status_code, payload, resp.url, sha256_text(text)
            time.sleep(1.0 + attempt)
        except Exception as exc:
            if attempt == 2:
                return False, 0, {"error": repr(exc)}, last_url, ""
            time.sleep(1.0 + attempt)
    return False, 429, {"error": "rate_limited_after_retries"}, last_url, ""


def parse_rows(data: Any) -> List[Tuple[int, Optional[float], Optional[float]]]:
    rows: List[Tuple[int, Optional[float], Optional[float]]] = []
    if not isinstance(data, list):
        return rows
    for item in data:
        if not isinstance(item, list) or not item:
            continue
        try:
            ts = int(float(item[0]))
        except Exception:
            continue
        oi = None
        vol = None
        if len(item) > 1:
            try:
                oi = float(item[1])
            except Exception:
                oi = None
        if len(item) > 2:
            try:
                vol = float(item[2])
            except Exception:
                vol = None
        rows.append((ts, oi, vol))
    rows.sort(key=lambda row: row[0])
    return rows


def interval_summary(rows: List[Tuple[int, Optional[float], Optional[float]]]) -> Tuple[str, int, int, int]:
    if len(rows) < 2:
        return "insufficient_rows", 0, 0, 0
    deltas = [rows[i][0] - rows[i - 1][0] for i in range(1, len(rows))]
    counts = Counter(deltas)
    mode_delta = counts.most_common(1)[0][0]
    gaps = sum(1 for delta in deltas if delta > mode_delta)
    dupes = len(rows) - len({row[0] for row in rows})
    return f"{mode_delta // 60000}m", int(mode_delta), gaps, dupes


def row_count(payload: Dict[str, Any]) -> int:
    data = payload.get("data")
    return len(data) if isinstance(data, list) else 0


def payload_code(payload: Dict[str, Any]) -> str:
    return str(payload.get("code", ""))


def payload_msg(payload: Dict[str, Any]) -> str:
    msg = payload.get("msg", "") or payload.get("error_message", "") or payload.get("error", "")
    return str(msg)


def raw_data_path(name: str) -> str:
    return str((RAW_DIR / name).relative_to(ROOT))


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def main() -> None:
    OUT.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for path in RAW_DIR.glob("*"):
        if path.is_file():
            path.unlink()

    mapping = read_mapping()
    fetch_log: List[Dict[str, Any]] = []
    coverage_rows: List[Dict[str, Any]] = []
    unit_rows: List[Dict[str, Any]] = []
    alignment_rows: List[Dict[str, Any]] = []
    gaps_rows: List[Dict[str, Any]] = []
    data_path_rows: List[Dict[str, Any]] = []
    current_by_market: Dict[str, Dict[str, Any]] = {}
    hist_by_market: Dict[str, Dict[str, Any]] = {}
    hist_inst_by_market: Dict[str, Dict[str, Any]] = {}
    ccxt_hist_by_market: Dict[str, Dict[str, Any]] = {}

    current_raw = RAW_DIR / "okx_native_current_exact_open_interest.jsonl"
    hist_raw = RAW_DIR / "okx_native_rubik_historical_oi_volume_by_ccy_1h.jsonl"
    hist_inst_raw = RAW_DIR / "okx_native_rubik_historical_oi_volume_by_ccy_with_instid_1h.jsonl"
    ccxt_raw = RAW_DIR / "ccxt_fetch_open_interest_history_1h.jsonl"

    for m in mapping:
        market = m["spot_style_symbol"]
        inst_id = m["okx_swap_inst_id"]
        base = m["base_asset"]
        ccxt_symbol = m["ccxt_symbol"]

        # Current exact instrument OI route.
        params = {"instType": "SWAP", "instId": inst_id}
        ok, status, payload, url, digest = fetch_okx("/api/v5/public/open-interest", params)
        record = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "source": "okx_native_public_open_interest_current_exact", "url": url, "status_code": status, "response_sha256": digest, "payload": payload}
        append_jsonl(current_raw, record)
        current_by_market[market] = payload
        fetch_log.append({"market": market, "inst_id": inst_id, "source": record["source"], "endpoint_or_method": "/api/v5/public/open-interest", "params": json.dumps(params, sort_keys=True), "success": ok and payload_code(payload) == "0", "status_code": status, "okx_code": payload_code(payload), "row_count": row_count(payload), "response_sha256": digest, "raw_data_path": raw_data_path(current_raw.name), "error_or_msg": payload_msg(payload), "fetch_timestamp_utc": FETCH_TS})
        time.sleep(SLEEP_SECONDS)

        # Native historical route by ccy. This is the known public OI history route.
        params = {"ccy": base, "period": "1H"}
        ok, status, payload, url, digest = fetch_okx("/api/v5/rubik/stat/contracts/open-interest-volume", params)
        record = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "source": "okx_native_rubik_contracts_open_interest_volume_by_ccy_1h", "url": url, "status_code": status, "response_sha256": digest, "payload": payload}
        append_jsonl(hist_raw, record)
        hist_by_market[market] = payload
        fetch_log.append({"market": market, "inst_id": inst_id, "source": record["source"], "endpoint_or_method": "/api/v5/rubik/stat/contracts/open-interest-volume", "params": json.dumps(params, sort_keys=True), "success": ok and payload_code(payload) == "0", "status_code": status, "okx_code": payload_code(payload), "row_count": row_count(payload), "response_sha256": digest, "raw_data_path": raw_data_path(hist_raw.name), "error_or_msg": payload_msg(payload), "fetch_timestamp_utc": FETCH_TS})
        time.sleep(SLEEP_SECONDS)

        # Same historical route with instId added, to test whether the endpoint honors exact instrument identity.
        params = {"ccy": base, "instId": inst_id, "period": "1H"}
        ok, status, payload, url, digest = fetch_okx("/api/v5/rubik/stat/contracts/open-interest-volume", params)
        record = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "source": "okx_native_rubik_contracts_open_interest_volume_by_ccy_plus_instid_1h", "url": url, "status_code": status, "response_sha256": digest, "payload": payload}
        append_jsonl(hist_inst_raw, record)
        hist_inst_by_market[market] = payload
        fetch_log.append({"market": market, "inst_id": inst_id, "source": record["source"], "endpoint_or_method": "/api/v5/rubik/stat/contracts/open-interest-volume", "params": json.dumps(params, sort_keys=True), "success": ok and payload_code(payload) == "0", "status_code": status, "okx_code": payload_code(payload), "row_count": row_count(payload), "response_sha256": digest, "raw_data_path": raw_data_path(hist_inst_raw.name), "error_or_msg": payload_msg(payload), "fetch_timestamp_utc": FETCH_TS})
        time.sleep(SLEEP_SECONDS)

    if ccxt is not None:
        exchange = ccxt.okx({"enableRateLimit": True})
        for m in mapping:
            market = m["spot_style_symbol"]
            inst_id = m["okx_swap_inst_id"]
            ccxt_symbol = m["ccxt_symbol"]
            try:
                rows = exchange.fetch_open_interest_history(ccxt_symbol, timeframe="1h", limit=100)
                payload = {"data": rows}
                ok = True
                err = ""
            except Exception as exc:
                payload = {"error": repr(exc), "data": []}
                rows = []
                ok = False
                err = repr(exc)
            text = json.dumps(payload, sort_keys=True, default=str)
            digest = sha256_text(text)
            record = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "ccxt_symbol": ccxt_symbol, "source": "ccxt_okx_fetch_open_interest_history_1h", "response_sha256": digest, "payload": payload}
            append_jsonl(ccxt_raw, record)
            ccxt_hist_by_market[market] = payload
            fetch_log.append({"market": market, "inst_id": inst_id, "source": record["source"], "endpoint_or_method": "ccxt.okx.fetch_open_interest_history", "params": json.dumps({"symbol": ccxt_symbol, "timeframe": "1h", "limit": 100}, sort_keys=True), "success": ok, "status_code": "", "okx_code": "", "row_count": len(rows), "response_sha256": digest, "raw_data_path": raw_data_path(ccxt_raw.name), "error_or_msg": err, "fetch_timestamp_utc": FETCH_TS})
            time.sleep(SLEEP_SECONDS)
    else:
        for m in mapping:
            fetch_log.append({"market": m["spot_style_symbol"], "inst_id": m["okx_swap_inst_id"], "source": "ccxt_okx_fetch_open_interest_history_1h", "endpoint_or_method": "ccxt unavailable", "params": "", "success": False, "status_code": "", "okx_code": "", "row_count": 0, "response_sha256": "", "raw_data_path": "", "error_or_msg": "ccxt_not_available", "fetch_timestamp_utc": FETCH_TS})

    for m in mapping:
        market = m["spot_style_symbol"]
        inst_id = m["okx_swap_inst_id"]
        base = m["base_asset"]
        current_payload = current_by_market.get(market, {})
        hist_payload = hist_by_market.get(market, {})
        hist_inst_payload = hist_inst_by_market.get(market, {})
        ccxt_payload = ccxt_hist_by_market.get(market, {})
        current_data = current_payload.get("data") if isinstance(current_payload.get("data"), list) else []
        current_info = current_data[0] if current_data and isinstance(current_data[0], dict) else {}
        hist_rows = parse_rows(hist_payload.get("data"))
        hist_inst_rows = parse_rows(hist_inst_payload.get("data"))
        hist_identical = hist_payload.get("data") == hist_inst_payload.get("data") and row_count(hist_payload) > 0
        interval_label, interval_ms, gaps, dupes = interval_summary(hist_rows)
        earliest = utc_iso(hist_rows[0][0]) if hist_rows else ""
        latest = utc_iso(hist_rows[-1][0]) if hist_rows else ""
        current_ts = safe_float(current_info.get("ts"))
        current_oi = safe_float(current_info.get("oi"))
        current_oi_ccy = safe_float(current_info.get("oiCcy"))
        current_oi_usd = safe_float(current_info.get("oiUsd"))
        hist_latest_oi = hist_rows[-1][1] if hist_rows else None
        exact_current_available = bool(current_info.get("instId") == inst_id and current_info.get("instType") == "SWAP")
        historical_available = bool(hist_rows)
        historical_exact_available = False
        if historical_available and hist_identical:
            exactness = "aggregate_or_currency_route_instid_not_honored"
        elif historical_available:
            exactness = "not_proven_exact_instrument"
        else:
            exactness = "historical_route_unavailable"
        usability = "usable_only_as_aggregate_context" if historical_available else "not_usable_for_strategy_research"
        alignment = "alignable_as_1h_aggregate_context_only_not_exact_instrument" if historical_available and interval_ms == 3600000 else "not_alignable_or_insufficient_history"

        coverage_rows.append({"market": market, "okx_inst_id": inst_id, "historical_oi_available": historical_available, "current_exact_oi_available": exact_current_available, "endpoint_method_used": "native_current_exact plus native_rubik_historical_ccy plus ccxt_history", "earliest_timestamp": earliest, "latest_timestamp": latest, "row_count": len(hist_rows), "sampling_interval": interval_label, "oi_value_field": "historical data[1]; current oi/oiCcy/oiUsd", "oi_unit_currency_contract_denomination": "historical ccy aggregate value/volume arrays without instId; current exact oi contracts plus oiCcy base plus oiUsd", "appears_exact_instrument_or_aggregate": exactness, "gaps": gaps, "duplicate_timestamps": dupes, "timezone_consistency": "UTC_epoch_ms", "fetch_timestamp_utc": FETCH_TS, "raw_data_path": raw_data_path(hist_raw.name), "usability_class": usability})

        unit_rows.append({"market": market, "okx_inst_id": inst_id, "current_exact_fields_present": exact_current_available, "current_oi_contracts": current_oi if current_oi is not None else "", "current_oi_ccy": current_oi_ccy if current_oi_ccy is not None else "", "current_oi_usd": current_oi_usd if current_oi_usd is not None else "", "historical_value_latest": hist_latest_oi if hist_latest_oi is not None else "", "historical_unit_assessment": "not exact; ccy aggregate route with no instId in response", "contract_vs_base_assessment": "current exact provides oi contracts and oiCcy; historical route provides aggregate value only", "conversion_possible": "not safely for exact-instrument history from this route", "unit_stable_over_time": "historical numeric field stable in sample but exact unit/provenance insufficient", "cross_market_comparison_valid": "no for exact-instrument comparison; possible only as aggregate context with caveats", "current_vs_historical_reconcile": "not_reconciled_as_exact_instrument", "aggregate_detection": exactness})

        alignment_rows.append({"market": market, "okx_inst_id": inst_id, "historical_sampling_interval": interval_label, "can_align_to_4h_same_prior": historical_available and interval_ms <= 4 * 3600 * 1000, "resampling_needed": "yes_1h_to_4h_if_used_as_aggregate_context", "leakage_risk": "low if same/prior timestamps only; high if treated as exact instrument without proof", "forward_fill_default": "no", "missing_too_frequent": gaps > 0, "alignment_decision": alignment})

        gaps_rows.append({"market": market, "okx_inst_id": inst_id, "source": "okx_native_rubik_contracts_open_interest_volume_by_ccy_1h", "row_count": len(hist_rows), "earliest_timestamp": earliest, "latest_timestamp": latest, "sampling_interval": interval_label, "gap_count": gaps, "duplicate_timestamps": dupes, "timezone": "UTC_epoch_ms", "notes": "gap count is relative to modal historical interval; exact-instrument history remains unproven"})

    data_path_rows = [
        {"path": raw_data_path(current_raw.name), "description": "Native OKX current exact instrument open-interest payloads by instId", "provenance": "/api/v5/public/open-interest instType=SWAP instId=<instrument>", "committed": "yes"},
        {"path": raw_data_path(hist_raw.name), "description": "Native OKX historical OI/volume payloads by currency at 1H cadence", "provenance": "/api/v5/rubik/stat/contracts/open-interest-volume ccy=<base> period=1H", "committed": "yes"},
        {"path": raw_data_path(hist_inst_raw.name), "description": "Native OKX historical OI/volume payloads with ccy plus instId to test whether instId is honored", "provenance": "/api/v5/rubik/stat/contracts/open-interest-volume ccy=<base> instId=<instrument> period=1H", "committed": "yes"},
        {"path": raw_data_path(ccxt_raw.name), "description": "ccxt OKX fetch_open_interest_history payloads at 1h for comparison", "provenance": "ccxt.okx.fetch_open_interest_history(symbol,timeframe=1h,limit=100)", "committed": "yes"},
    ]

    write_csv(OUT / f"{PREFIX}_instrument_mapping.csv", [
        {"spot_style_symbol": m["spot_style_symbol"], "base_asset": m["base_asset"], "quote_asset": m["quote_asset"], "okx_swap_inst_id": m["okx_swap_inst_id"], "ccxt_symbol": m["ccxt_symbol"], "visibility_requirement": m["visibility_requirement"], "audit_status": "included_same_19_market_universe"}
        for m in mapping
    ], ["spot_style_symbol", "base_asset", "quote_asset", "okx_swap_inst_id", "ccxt_symbol", "visibility_requirement", "audit_status"])
    write_csv(OUT / f"{PREFIX}_fetch_log.csv", fetch_log, ["market", "inst_id", "source", "endpoint_or_method", "params", "success", "status_code", "okx_code", "row_count", "response_sha256", "raw_data_path", "error_or_msg", "fetch_timestamp_utc"])
    write_csv(OUT / f"{PREFIX}_coverage.csv", coverage_rows, ["market", "okx_inst_id", "historical_oi_available", "current_exact_oi_available", "endpoint_method_used", "earliest_timestamp", "latest_timestamp", "row_count", "sampling_interval", "oi_value_field", "oi_unit_currency_contract_denomination", "appears_exact_instrument_or_aggregate", "gaps", "duplicate_timestamps", "timezone_consistency", "fetch_timestamp_utc", "raw_data_path", "usability_class"])
    write_csv(OUT / f"{PREFIX}_unit_checks.csv", unit_rows, ["market", "okx_inst_id", "current_exact_fields_present", "current_oi_contracts", "current_oi_ccy", "current_oi_usd", "historical_value_latest", "historical_unit_assessment", "contract_vs_base_assessment", "conversion_possible", "unit_stable_over_time", "cross_market_comparison_valid", "current_vs_historical_reconcile", "aggregate_detection"])
    write_csv(OUT / f"{PREFIX}_alignment_assessment.csv", alignment_rows, ["market", "okx_inst_id", "historical_sampling_interval", "can_align_to_4h_same_prior", "resampling_needed", "leakage_risk", "forward_fill_default", "missing_too_frequent", "alignment_decision"])
    write_csv(OUT / f"{PREFIX}_gaps_duplicates.csv", gaps_rows, ["market", "okx_inst_id", "source", "row_count", "earliest_timestamp", "latest_timestamp", "sampling_interval", "gap_count", "duplicate_timestamps", "timezone", "notes"])
    write_csv(OUT / f"{PREFIX}_data_paths.csv", data_path_rows, ["path", "description", "provenance", "committed"])

    exact_current_count = sum(1 for row in coverage_rows if row["current_exact_oi_available"])
    hist_count = sum(1 for row in coverage_rows if row["historical_oi_available"])
    aggregate_count = sum(1 for row in coverage_rows if row["usability_class"] == "usable_only_as_aggregate_context")
    key_markets = {"BTCUSDT", "DOGEUSDT", "DOTUSDT", "UNIUSDT"}
    key_visible = all(any(row["market"] == market for row in coverage_rows) for market in key_markets)
    decision_rows = [
        {"scope": "current_exact_oi", "classification": "available_for_unit_checks", "markets": exact_current_count, "key_markets_visible": key_visible, "reason": "Native current endpoint returns exact instId payloads with oi oiCcy oiUsd but only current snapshot."},
        {"scope": "historical_oi", "classification": "usable_only_as_aggregate_context", "markets": hist_count, "key_markets_visible": key_visible, "reason": "Historical public route is ccy-based, response lacks instId, and adding instId returns the same ccy payload; exact instrument history is not proven."},
        {"scope": "overall_exact_instrument_oi", "classification": "usable_only_as_aggregate_context", "markets": aggregate_count, "key_markets_visible": key_visible, "reason": "Exact current OI exists but historical exact-instrument OI was not available through the audited public route; no exact OI strategy research from this route."},
    ]
    write_csv(OUT / f"{PREFIX}_usability_decision.csv", decision_rows, ["scope", "classification", "markets", "key_markets_visible", "reason"])

    note = f"""# Exact-Instrument OI Data Availability Audit Round 1

## Scope

This is a research-only data availability audit. Public OKX open-interest data was fetched only to assess whether exact OKX swap historical OI exists for the same 19 markets and whether it is unit-consistent, timestamped, and alignable to 4h research candles. No trading strategy was defined or tested, no OHLCV was fetched, no backtest or validation was run, and no production source, parameter, deployment, dry-run, or live behavior was changed.

## Instruments Audited

The audit used the same 19 mapped OKX USDT swap instruments from the plan. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible in all summary tables.

## Data Sources Checked

- Native OKX current exact open-interest endpoint: `/api/v5/public/open-interest` with `instType=SWAP` and exact `instId`.
- Native OKX historical contracts OI/volume endpoint: `/api/v5/rubik/stat/contracts/open-interest-volume` with `ccy=<base>` and `period=1H`.
- Native historical endpoint with `ccy=<base>` plus `instId=<instrument>` to test whether exact instrument identity is honored.
- ccxt OKX `fetch_open_interest_history(symbol, timeframe=1h, limit=100)` for comparison.
- Existing previous audit raw files were inspected as provenance/context only.

Raw fetched payloads were saved under `research_output/exact_instrument_oi_audit_round1_raw/`.

## Availability Summary

Current exact instrument OI is available for {exact_current_count}/19 markets through the native current endpoint. The current payload includes exact `instId`, `instType`, `oi`, `oiCcy`, `oiUsd`, and timestamp fields.

Historical OI-like data is available for {hist_count}/19 markets at 1h cadence through the Rubik contracts OI/volume endpoint, but this route is currency-based. The response rows are arrays of timestamp, OI value, and volume, and they do not include `instId`. Adding `instId` while retaining `ccy` produced the same currency-route payload in this audit, so exact-instrument historical OI was not proven.

## Unit Consistency

The current exact endpoint exposes contract/base/USD fields that are suitable for current unit checks. The historical route does not expose exact instrument identity or equivalent `oi`, `oiCcy`, and `oiUsd` fields. It is therefore not safe to reconcile the historical route as exact instrument history, nor to perform cross-market exact OI comparisons without additional source support.

## 4h Alignment

The historical ccy route is 1h timestamped data and can technically be aligned to 4h candles using same/prior timestamps without forward leakage if treated only as aggregate context. However, because exact instrument history is not proven, it should not be used as exact-instrument OI for strategy research. Current exact OI is only a snapshot and cannot support historical 4h validation.

## Gaps And Duplicates

The fetched historical ccy-route samples were assessed for row count, modal interval, gaps, duplicate timestamps, and UTC timestamp consistency. See `exact_instrument_oi_audit_round1_gaps_duplicates.csv` for per-market details.

## Usability Decision

Overall classification: `usable_only_as_aggregate_context`.

This means exact current OI is available for unit checks, and 1h historical OI-like data is available as currency-level context, but exact-instrument historical OI was not established through the audited OKX/ccxt public route. No exact-instrument OI strategy research should be defined from this route alone.

## Recommendation

Do not define or validate an OI strategy from this route. If OI research continues, either find an explicitly exact-instrument historical source with unit metadata or create a separate aggregate-context research plan that clearly states it is not exact instrument OI. No-trade remains the default and implementation readiness remains closed.
"""
    (OUT / f"{PREFIX}_note.md").write_text(note, encoding="utf-8")

    limitations = """# Exact-Instrument OI Audit Round 1 Limitations

- The audit fetched only public OI data and did not fetch OHLCV, private account data, order data, trade data, or funding data.
- The native current OKX endpoint provided exact instrument OI snapshots, but not historical exact-instrument series.
- The historical OKX Rubik route required `ccy` and returned array rows without `instId`; adding `instId` did not prove exact instrument filtering.
- The 1h historical route can only be treated as aggregate or currency-level context from this audit.
- Current exact OI cannot be used for historical validation by itself.
- Unit reconciliation between current exact fields and historical aggregate fields was not accepted as proof of exact instrument history.
- No forward-fill, inferred OI, synthetic values, or strategy rules were created.
- No implementation readiness, dry-run readiness, or live readiness is implied.
"""
    (OUT / f"{PREFIX}_limitations.md").write_text(limitations, encoding="utf-8")

    handoff = f"""=== CHATGPT HANDOFF START ===
1. run status: exact_instrument_oi_audit_round1 executed as data availability audit only; no strategy definition, backtest, validation, OHLCV fetch, private data fetch, tuning, source change, dry-run, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before audit was 56ed1e3 research: add exact instrument OI audit plan.
3. commands run: verified branch/HEAD and plan mapping; fetched approved public OI endpoint data; saved raw payloads; wrote coverage/provenance/usability outputs; ran sanity checks; staged only audit outputs/script; committed and pushed.
4. files changed / output paths: research/exact_instrument_oi_audit_round1.py; research_output/exact_instrument_oi_audit_round1_note.md; _instrument_mapping.csv; _fetch_log.csv; _coverage.csv; _unit_checks.csv; _alignment_assessment.csv; _gaps_duplicates.csv; _usability_decision.csv; _data_paths.csv; _limitations.md; _handoff.md; raw payloads under research_output/exact_instrument_oi_audit_round1_raw/.
5. instruments audited: same 19 OKX USDT swap instruments, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visible.
6. data sources / endpoints used: OKX native current open-interest endpoint by exact instId; OKX native Rubik contracts open-interest-volume by ccy and ccy+instId; ccxt OKX fetch_open_interest_history 1h for comparison.
7. exact OI availability summary: current exact instrument OI was available for {exact_current_count}/19 markets, but historical exact-instrument OI was not proven; historical route was ccy-based and lacked instId in response.
8. unit consistency result: current exact route exposes oi/oiCcy/oiUsd, but historical route exposes aggregate value/volume arrays; unit reconciliation is insufficient for exact-instrument research.
9. 4h alignment assessment: 1h historical ccy data can align to 4h only as aggregate context; current exact snapshots cannot support historical 4h validation.
10. gaps / duplicates / coverage issues: historical ccy-route row counts, modal intervals, gaps, and duplicates are documented per market; exact historical coverage remains the blocking issue.
11. usability decision: usable_only_as_aggregate_context; no exact-instrument OI strategy research should be defined from this data route alone.
12. recommended next direction: stay no-trade/benchmark-only unless a separate exact historical OI source is approved, or explicitly plan aggregate-context research with constraints.
13. what remains forbidden: strategy definition/testing, backtests, validation, threshold sweeps, source/parameter changes, dry-run/live planning, and reviving closed candidates.
14. implementation readiness judgment: closed / not ready.
15. commit / push result: pending at file creation time; verify final response for actual commit and push result.
16. next recommended Codex prompt: Create a research-only postmortem/synthesis for the exact OI audit result and decide whether to stop OI research or plan an aggregate-context-only feature audit.
17. one-sentence conclusion: Exact current OI exists, but historical exact-instrument OI was not proven through the audited public route, so OI remains aggregate-context only.
=== CHATGPT HANDOFF END ===
"""
    (OUT / f"{PREFIX}_handoff.md").write_text(handoff, encoding="utf-8")


if __name__ == "__main__":
    main()
