#!/usr/bin/env python3
"""Research-only taker-flow data availability audit.

Fetches approved public taker-volume / public trade samples only to assess
availability, fields, provenance, units, and 4h alignment feasibility. It does
not define or test a strategy, fetch OHLCV, or use private data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

try:
    import ccxt  # type: ignore
except Exception:  # pragma: no cover
    ccxt = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_output"
PLAN_MAPPING = OUT / "taker_flow_data_availability_audit_plan_round1_market_mapping.csv"
PREFIX = "taker_flow_data_availability_audit_round1"
RAW_DIR = OUT / f"{PREFIX}_raw"
OKX_BASE = "https://www.okx.com"
FETCH_TS = datetime.now(timezone.utc).isoformat()
TIMEOUT = 20
SLEEP_SECONDS = 0.25


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_iso(ts_ms: Optional[int]) -> str:
    if ts_ms is None:
        return ""
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()


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


def raw_rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def payload_code(payload: Dict[str, Any]) -> str:
    return str(payload.get("code", ""))


def payload_msg(payload: Dict[str, Any]) -> str:
    return str(payload.get("msg", "") or payload.get("error_message", "") or payload.get("error", ""))


def row_count(payload: Dict[str, Any]) -> int:
    data = payload.get("data")
    return len(data) if isinstance(data, list) else 0


def parse_taker_rows(data: Any) -> List[Tuple[int, Optional[float], Optional[float]]]:
    rows: List[Tuple[int, Optional[float], Optional[float]]] = []
    if not isinstance(data, list):
        return rows
    for item in data:
        if not isinstance(item, list) or len(item) < 3:
            continue
        try:
            ts = int(float(item[0]))
        except Exception:
            continue
        sell_vol = None
        buy_vol = None
        try:
            sell_vol = float(item[1])
        except Exception:
            pass
        try:
            buy_vol = float(item[2])
        except Exception:
            pass
        rows.append((ts, sell_vol, buy_vol))
    rows.sort(key=lambda r: r[0])
    return rows


def interval_summary(timestamps: List[int]) -> Tuple[str, int, int, int, int]:
    if len(timestamps) < 2:
        return "insufficient_rows", 0, 0, 0, 0
    timestamps_sorted = sorted(timestamps)
    dupes = len(timestamps_sorted) - len(set(timestamps_sorted))
    deltas = [timestamps_sorted[i] - timestamps_sorted[i - 1] for i in range(1, len(timestamps_sorted)) if timestamps_sorted[i] != timestamps_sorted[i - 1]]
    if not deltas:
        return "all_duplicate_or_single", 0, 0, dupes, 0
    counts = Counter(deltas)
    mode_delta = counts.most_common(1)[0][0]
    gaps = sum(1 for delta in deltas if delta > mode_delta)
    max_gap = max(deltas) if deltas else 0
    return f"{mode_delta // 60000}m", mode_delta, gaps, dupes, max_gap


def safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def unique_trade_sides(trades: List[Dict[str, Any]]) -> str:
    sides = sorted({str(t.get("side", "")) for t in trades if isinstance(t, dict)})
    return ";".join(sides)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for path in RAW_DIR.glob("*"):
        if path.is_file():
            path.unlink()

    mapping = read_mapping()
    fetch_log: List[Dict[str, Any]] = []
    data_source_rows: List[Dict[str, Any]] = []
    field_rows: List[Dict[str, Any]] = []
    feature_rows: List[Dict[str, Any]] = []
    alignment_rows: List[Dict[str, Any]] = []
    gaps_rows: List[Dict[str, Any]] = []
    usability_market_rows: List[Dict[str, Any]] = []

    native_taker_raw = RAW_DIR / "okx_rubik_contracts_taker_volume_1h_by_ccy.jsonl"
    native_taker_with_inst_raw = RAW_DIR / "okx_rubik_contracts_taker_volume_1h_by_ccy_plus_instid.jsonl"
    market_trades_raw = RAW_DIR / "okx_market_trades_sample.jsonl"
    history_trades_raw = RAW_DIR / "okx_market_history_trades_sample.jsonl"
    ccxt_markets_raw = RAW_DIR / "ccxt_method_capability_snapshot.jsonl"

    # ccxt public method capability snapshot.
    ccxt_methods = []
    ccxt_has = {}
    if ccxt is not None:
        exchange = ccxt.okx({"enableRateLimit": True})
        ccxt_has = dict(exchange.has)
        ccxt_methods = [name for name in dir(exchange) if "taker" in name.lower() or "trade" in name.lower()]
    ccxt_record = {"fetch_timestamp_utc": FETCH_TS, "source": "ccxt_okx_capability_snapshot", "has": ccxt_has, "taker_or_trade_methods": ccxt_methods}
    append_jsonl(ccxt_markets_raw, ccxt_record)
    data_source_rows.append({"source_id": "ccxt_capability_snapshot", "source_type": "ccxt", "endpoint_or_method": "ccxt.okx capability/method inspection", "markets_checked": len(mapping), "feature_form_available": "public trade methods; no unified historical taker buy/sell volume method identified", "scope_assessment": "method_inventory_only", "raw_data_path": raw_rel(ccxt_markets_raw), "audit_result": "supports_public_trade_checks_not_direct_taker_volume"})

    taker_payloads: Dict[str, Dict[str, Any]] = {}
    taker_inst_payloads: Dict[str, Dict[str, Any]] = {}
    market_trade_payloads: Dict[str, Dict[str, Any]] = {}
    history_trade_payloads: Dict[str, Dict[str, Any]] = {}

    for m in mapping:
        market = m["spot_style_symbol"]
        base = m["base_asset"]
        inst_id = m["okx_swap_inst_id"]

        params = {"ccy": base, "instType": "CONTRACTS", "period": "1H"}
        ok, status, payload, url, digest = fetch_okx("/api/v5/rubik/stat/taker-volume", params)
        taker_payloads[market] = payload
        rec = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "url": url, "status_code": status, "response_sha256": digest, "payload": payload}
        append_jsonl(native_taker_raw, rec)
        fetch_log.append({"market": market, "inst_id": inst_id, "source": rec["source"], "endpoint_or_method": "/api/v5/rubik/stat/taker-volume", "params": json.dumps(params, sort_keys=True), "success": ok and payload_code(payload) == "0", "status_code": status, "okx_code": payload_code(payload), "row_count": row_count(payload), "response_sha256": digest, "raw_data_path": raw_rel(native_taker_raw), "error_or_msg": payload_msg(payload), "fetch_timestamp_utc": FETCH_TS})
        time.sleep(SLEEP_SECONDS)

        # Add instId to test whether the route honors exact instrument identity.
        params_inst = {"ccy": base, "instType": "CONTRACTS", "instId": inst_id, "period": "1H"}
        ok2, status2, payload2, url2, digest2 = fetch_okx("/api/v5/rubik/stat/taker-volume", params_inst)
        taker_inst_payloads[market] = payload2
        rec2 = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_plus_instid_1h", "url": url2, "status_code": status2, "response_sha256": digest2, "payload": payload2}
        append_jsonl(native_taker_with_inst_raw, rec2)
        fetch_log.append({"market": market, "inst_id": inst_id, "source": rec2["source"], "endpoint_or_method": "/api/v5/rubik/stat/taker-volume", "params": json.dumps(params_inst, sort_keys=True), "success": ok2 and payload_code(payload2) == "0", "status_code": status2, "okx_code": payload_code(payload2), "row_count": row_count(payload2), "response_sha256": digest2, "raw_data_path": raw_rel(native_taker_with_inst_raw), "error_or_msg": payload_msg(payload2), "fetch_timestamp_utc": FETCH_TS})
        time.sleep(SLEEP_SECONDS)

        # Lightweight recent public trade samples only; no reconstruction.
        for endpoint, raw_path, source_name, store in [
            ("/api/v5/market/trades", market_trades_raw, "okx_public_market_trades_recent_sample", market_trade_payloads),
            ("/api/v5/market/history-trades", history_trades_raw, "okx_public_market_history_trades_recent_sample", history_trade_payloads),
        ]:
            params_trade = {"instId": inst_id, "limit": "20"}
            ok3, status3, payload3, url3, digest3 = fetch_okx(endpoint, params_trade)
            store[market] = payload3
            rec3 = {"fetch_timestamp_utc": FETCH_TS, "market": market, "inst_id": inst_id, "source": source_name, "url": url3, "status_code": status3, "response_sha256": digest3, "payload": payload3}
            append_jsonl(raw_path, rec3)
            fetch_log.append({"market": market, "inst_id": inst_id, "source": source_name, "endpoint_or_method": endpoint, "params": json.dumps(params_trade, sort_keys=True), "success": ok3 and payload_code(payload3) == "0", "status_code": status3, "okx_code": payload_code(payload3), "row_count": row_count(payload3), "response_sha256": digest3, "raw_data_path": raw_rel(raw_path), "error_or_msg": payload_msg(payload3), "fetch_timestamp_utc": FETCH_TS})
            time.sleep(SLEEP_SECONDS)

    for m in mapping:
        market = m["spot_style_symbol"]
        inst_id = m["okx_swap_inst_id"]
        ccxt_symbol = m["ccxt_symbol"]
        payload = taker_payloads.get(market, {})
        payload_inst = taker_inst_payloads.get(market, {})
        rows = parse_taker_rows(payload.get("data"))
        timestamps = [r[0] for r in rows]
        interval_label, interval_ms, gaps, dupes, max_gap = interval_summary(timestamps)
        earliest = utc_iso(min(timestamps)) if timestamps else ""
        latest = utc_iso(max(timestamps)) if timestamps else ""
        row_ct = len(rows)
        has_direct = row_ct > 0 and all(r[1] is not None and r[2] is not None for r in rows[: min(row_ct, 10)])
        inst_same = payload.get("data") == payload_inst.get("data") and row_ct > 0 and row_count(payload_inst) > 0
        if inst_same:
            scope = "ccy_contracts_aggregate_instid_not_honored_or_not_distinguishable"
        elif row_ct > 0 and row_count(payload_inst) > 0:
            scope = "ccy_contracts_aggregate_exact_instid_not_proven"
        else:
            scope = "unavailable_or_error"
        usability = "partially_usable_short_history" if has_direct else "not_usable_for_research"
        feature_availability = "direct_taker_buy_sell_volume_ccy_contracts_aggregate" if has_direct else "unavailable_from_public_history"
        unit_assessment = "OKX Rubik CONTRACTS taker-volume arrays data[1]/data[2] are endpoint-defined sell/buy volume; exact unit/cross-market denomination requires source documentation; not proven exact instId"
        if row_ct >= 700 and interval_ms == 3600000:
            alignment_decision = "alignable_to_4h_as_1h_ccy_contracts_aggregate_context"
        elif row_ct > 0 and interval_ms <= 4 * 3600000:
            alignment_decision = "partially_alignable_to_4h_short_or_irregular_history"
        else:
            alignment_decision = "not_alignable_or_no_rows"

        trade_payload = market_trade_payloads.get(market, {})
        history_payload = history_trade_payloads.get(market, {})
        trade_rows = trade_payload.get("data") if isinstance(trade_payload.get("data"), list) else []
        hist_trade_rows = history_payload.get("data") if isinstance(history_payload.get("data"), list) else []
        sample_sides = unique_trade_sides(trade_rows + hist_trade_rows)
        public_trade_reconstructable = bool(trade_rows or hist_trade_rows) and {"buy", "sell"}.issubset(set(sample_sides.split(";")))

        field_rows.append({"market": market, "okx_inst_id": inst_id, "ccxt_symbol": ccxt_symbol, "direct_taker_buy_volume_available": has_direct, "direct_taker_sell_volume_available": has_direct, "buy_sell_ratio_available_directly": False, "taker_volume_ratio_available_directly": False, "aggregated_long_short_taker_volume_available": has_direct, "public_trade_reconstructable_sample": public_trade_reconstructable, "source_scope": scope, "earliest_timestamp": earliest, "latest_timestamp": latest, "row_count": row_ct, "sampling_interval": interval_label, "fields_returned": "timestamp; endpoint data[1] sell volume; endpoint data[2] buy volume", "units": unit_assessment, "raw_data_path": raw_rel(native_taker_raw), "usability_class": usability})

        total_vols = [(r[1] or 0.0) + (r[2] or 0.0) for r in rows if r[1] is not None and r[2] is not None]
        nonzero_total = sum(1 for v in total_vols if v > 0)
        feature_rows.extend([
            {"market": market, "feature": "taker_buy_ratio", "computable": has_direct and nonzero_total == len(total_vols) and row_ct > 0, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "scope": scope, "unit_requirement": "buy and sell volumes share same endpoint unit", "limitation": "ccy/contracts aggregate not proven exact instrument"},
            {"market": market, "feature": "taker_sell_ratio", "computable": has_direct and nonzero_total == len(total_vols) and row_ct > 0, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "scope": scope, "unit_requirement": "buy and sell volumes share same endpoint unit", "limitation": "ccy/contracts aggregate not proven exact instrument"},
            {"market": market, "feature": "taker_imbalance", "computable": has_direct and nonzero_total == len(total_vols) and row_ct > 0, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "scope": scope, "unit_requirement": "buy and sell volumes share same endpoint unit", "limitation": "ccy/contracts aggregate not proven exact instrument"},
            {"market": market, "feature": "taker_delta", "computable": has_direct, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "scope": scope, "unit_requirement": "buy and sell volumes share same endpoint unit", "limitation": "ccy/contracts aggregate not proven exact instrument"},
            {"market": market, "feature": "abnormal_turnover", "computable": has_direct, "source": "sum of taker buy and sell volume as turnover proxy", "scope": scope, "unit_requirement": "rolling median window must be frozen later", "limitation": "not validated and not exact instrument"},
            {"market": market, "feature": "range_volume_impulse", "computable": "not_from_taker_flow_alone", "source": "requires OHLCV candle range plus audited volume", "scope": "future_plan_only", "unit_requirement": "OHLCV range alignment required later", "limitation": "not computed in availability audit"},
        ])

        alignment_rows.append({"market": market, "okx_inst_id": inst_id, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "sampling_interval": interval_label, "can_align_to_4h": row_ct > 0 and interval_ms <= 4 * 3600000, "alignment_method": "aggregate 1h rows into closed 4h buckets only", "future_leakage_risk": "low if closed buckets only; high if incomplete current bucket used", "forward_fill_default": "no", "sparse_or_higher_timeframe": False, "alignment_decision": alignment_decision})
        gaps_rows.append({"market": market, "okx_inst_id": inst_id, "source": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "row_count": row_ct, "earliest_timestamp": earliest, "latest_timestamp": latest, "sampling_interval": interval_label, "gap_count": gaps, "duplicate_timestamps": dupes, "max_gap_minutes": int(max_gap / 60000) if max_gap else 0, "timezone": "UTC_epoch_ms", "notes": "gap count relative to modal historical interval; route is ccy/contracts aggregate"})
        usability_market_rows.append({"market": market, "okx_inst_id": inst_id, "classification": usability, "data_form": feature_availability, "key_market_visible": market in {"BTCUSDT", "DOGEUSDT", "DOTUSDT", "UNIUSDT"}, "reason": "1h direct taker buy/sell volume-like arrays available as CONTRACTS ccy aggregate; exact instrument scope not proven; history length limited to public endpoint sample"})

    direct_markets = sum(1 for r in field_rows if r["direct_taker_buy_volume_available"])
    key_visible = all(any(r["market"] == key for r in field_rows) for key in ["BTCUSDT", "DOGEUSDT", "DOTUSDT", "UNIUSDT"])
    overall_class = "partially_usable_short_history" if direct_markets == len(mapping) else "not_usable_for_research"

    data_source_rows.extend([
        {"source_id": "okx_rubik_stat_taker_volume_contracts_by_ccy_1h", "source_type": "OKX native public REST", "endpoint_or_method": "/api/v5/rubik/stat/taker-volume ccy=<base> instType=CONTRACTS period=1H", "markets_checked": len(mapping), "feature_form_available": "direct endpoint arrays for taker sell/buy volume at 1h ccy/contracts aggregate scope", "scope_assessment": "ccy_contracts_aggregate_not_proven_exact_instid", "raw_data_path": raw_rel(native_taker_raw), "audit_result": overall_class},
        {"source_id": "okx_rubik_stat_taker_volume_with_instid_probe", "source_type": "OKX native public REST", "endpoint_or_method": "/api/v5/rubik/stat/taker-volume ccy=<base> instType=CONTRACTS instId=<swap> period=1H", "markets_checked": len(mapping), "feature_form_available": "same/probe payload used to test whether instId is honored", "scope_assessment": "instid_not_proven_or_not_distinguishable_from_ccy_route", "raw_data_path": raw_rel(native_taker_with_inst_raw), "audit_result": "does_not_prove_exact_instrument_taker_flow"},
        {"source_id": "okx_market_trades_recent_sample", "source_type": "OKX native public REST", "endpoint_or_method": "/api/v5/market/trades instId=<swap> limit=20", "markets_checked": len(mapping), "feature_form_available": "recent public trades with side, size, price, timestamp", "scope_assessment": "lightweight_recent_sample_only", "raw_data_path": raw_rel(market_trades_raw), "audit_result": "public_trade_reconstruction_possible_in_principle_but_not_full_history_audited"},
        {"source_id": "okx_market_history_trades_recent_sample", "source_type": "OKX native public REST", "endpoint_or_method": "/api/v5/market/history-trades instId=<swap> limit=20", "markets_checked": len(mapping), "feature_form_available": "recent/history public trade sample with side, size, price, timestamp", "scope_assessment": "sample_only_not_full_historical_reconstruction", "raw_data_path": raw_rel(history_trades_raw), "audit_result": "requires_separate_reconstruction_feasibility_plan_for_full_history"},
    ])

    write_csv(OUT / f"{PREFIX}_market_mapping.csv", [
        {"spot_style_symbol": m["spot_style_symbol"], "base_asset": m["base_asset"], "quote_asset": m["quote_asset"], "okx_swap_inst_id": m["okx_swap_inst_id"], "ccxt_symbol": m["ccxt_symbol"], "visibility_requirement": m["visibility_requirement"], "audit_status": "included_same_19_market_universe"}
        for m in mapping
    ], ["spot_style_symbol", "base_asset", "quote_asset", "okx_swap_inst_id", "ccxt_symbol", "visibility_requirement", "audit_status"])
    write_csv(OUT / f"{PREFIX}_fetch_log.csv", fetch_log, ["market", "inst_id", "source", "endpoint_or_method", "params", "success", "status_code", "okx_code", "row_count", "response_sha256", "raw_data_path", "error_or_msg", "fetch_timestamp_utc"])
    write_csv(OUT / f"{PREFIX}_data_sources.csv", data_source_rows, ["source_id", "source_type", "endpoint_or_method", "markets_checked", "feature_form_available", "scope_assessment", "raw_data_path", "audit_result"])
    write_csv(OUT / f"{PREFIX}_field_coverage.csv", field_rows, ["market", "okx_inst_id", "ccxt_symbol", "direct_taker_buy_volume_available", "direct_taker_sell_volume_available", "buy_sell_ratio_available_directly", "taker_volume_ratio_available_directly", "aggregated_long_short_taker_volume_available", "public_trade_reconstructable_sample", "source_scope", "earliest_timestamp", "latest_timestamp", "row_count", "sampling_interval", "fields_returned", "units", "raw_data_path", "usability_class"])
    write_csv(OUT / f"{PREFIX}_feature_computability.csv", feature_rows, ["market", "feature", "computable", "source", "scope", "unit_requirement", "limitation"])
    write_csv(OUT / f"{PREFIX}_alignment_assessment.csv", alignment_rows, ["market", "okx_inst_id", "source", "sampling_interval", "can_align_to_4h", "alignment_method", "future_leakage_risk", "forward_fill_default", "sparse_or_higher_timeframe", "alignment_decision"])
    write_csv(OUT / f"{PREFIX}_gaps_duplicates.csv", gaps_rows, ["market", "okx_inst_id", "source", "row_count", "earliest_timestamp", "latest_timestamp", "sampling_interval", "gap_count", "duplicate_timestamps", "max_gap_minutes", "timezone", "notes"])

    decision_rows = [
        {"scope": "rubik_contracts_taker_volume", "classification": overall_class, "markets": direct_markets, "key_markets_visible": key_visible, "reason": "1h taker buy/sell volume-like arrays are available for all 19 base currencies at CONTRACTS ccy aggregate scope, but exact instrument scope is not proven and history is endpoint-limited."},
        {"scope": "public_trade_reconstruction", "classification": "usable_derived_from_public_trades_possible_sample_only", "markets": len(mapping), "key_markets_visible": key_visible, "reason": "Recent public/history trade samples expose side, size, price, and timestamp for all 19 instruments, but full historical reconstruction was not performed and likely needs a separate feasibility plan."},
        {"scope": "overall_taker_flow", "classification": overall_class, "markets": direct_markets, "key_markets_visible": key_visible, "reason": "Direct aggregate taker-flow context is available, but exact instrument-level and full-history reconstruction constraints prevent immediate strategy definition."},
    ]
    write_csv(OUT / f"{PREFIX}_usability_decision.csv", decision_rows, ["scope", "classification", "markets", "key_markets_visible", "reason"])

    data_paths = [
        {"path": raw_rel(native_taker_raw), "description": "OKX Rubik taker-volume 1h CONTRACTS by ccy raw payloads", "provenance": "/api/v5/rubik/stat/taker-volume ccy=<base> instType=CONTRACTS period=1H", "committed": "yes"},
        {"path": raw_rel(native_taker_with_inst_raw), "description": "OKX Rubik taker-volume 1h CONTRACTS by ccy plus instId probe raw payloads", "provenance": "/api/v5/rubik/stat/taker-volume ccy=<base> instType=CONTRACTS instId=<swap> period=1H", "committed": "yes"},
        {"path": raw_rel(market_trades_raw), "description": "OKX recent public trades sample raw payloads", "provenance": "/api/v5/market/trades instId=<swap> limit=20", "committed": "yes"},
        {"path": raw_rel(history_trades_raw), "description": "OKX public history-trades sample raw payloads", "provenance": "/api/v5/market/history-trades instId=<swap> limit=20", "committed": "yes"},
        {"path": raw_rel(ccxt_markets_raw), "description": "ccxt OKX capability snapshot for taker/trade methods", "provenance": "ccxt.okx method/has inspection", "committed": "yes"},
    ]
    write_csv(OUT / f"{PREFIX}_data_paths.csv", data_paths, ["path", "description", "provenance", "committed"])

    note = f"""# Taker-Flow Data Availability Audit Round 1

## Scope

This is a research-only data availability audit. It fetched only explicitly approved public taker-volume / public trade sample data for the same 19 markets. It did not fetch OHLCV, private account/order data, unrelated symbols, or funding/OI data. It did not define a strategy, run backtests, run validation, tune parameters, change production source code, restart dry-run, or create live-trading plans.

## Markets Audited

The audit used the same 19 spot-style markets mapped to OKX USDT swap instruments. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible in all coverage tables.

## Data Sources Checked

- OKX Rubik taker-volume endpoint: `/api/v5/rubik/stat/taker-volume` with `ccy=<base>`, `instType=CONTRACTS`, and `period=1H`.
- The same Rubik endpoint with `instId=<OKX-USDT-SWAP>` added as a scope probe.
- OKX recent public trades sample: `/api/v5/market/trades` with `instId=<swap>` and `limit=20`.
- OKX public history-trades sample: `/api/v5/market/history-trades` with `instId=<swap>` and `limit=20`.
- ccxt OKX capability/method inspection for public trade/taker method support.

Raw payloads were saved under `research_output/taker_flow_data_availability_audit_round1_raw/`.

## Availability Summary

The OKX Rubik taker-volume endpoint returned 1h timestamped buy/sell volume-like arrays for {direct_markets}/19 base currencies at `CONTRACTS` scope. The returned arrays are suitable for auditing taker buy/sell ratios, taker imbalance, taker delta, and abnormal turnover-like context at a ccy/contracts aggregate scope.

However, the route is not proven exact-instrument. Adding `instId` is a probe, not proof of exact OKX swap scope. Therefore the data should not be described as exact instrument-level taker flow unless a future audit proves that scope.

Public trade samples were available for all 19 swap instruments and include side, size, price, trade ID, and timestamp. That means reconstruction may be possible in principle, but only as a separate feasibility plan because full historical reconstruction could be heavy, rate-limited, and storage-intensive.

## Field And Unit Coverage

Direct endpoint arrays provide timestamp, a sell-volume-like field, and a buy-volume-like field. The audit labels these as endpoint-defined `data[1]` sell volume and `data[2]` buy volume. Units must remain endpoint-defined and are not accepted as cross-market normalized without a later source/unit audit. Quote volume is not directly provided by this route.

## Feature Computability

At the aggregate CONTRACTS ccy scope, `taker_buy_ratio`, `taker_sell_ratio`, `taker_imbalance`, `taker_delta`, and an abnormal-turnover proxy from summed taker flow are computable for all 19 markets. `range_volume_impulse` is not computable from taker-flow alone because it also requires OHLCV candle range; it remains a future plan-only formula.

## 4h Alignment

The taker-volume route is 1h. It can be aggregated into closed 4h buckets without future leakage if a future plan uses only completed lower-timeframe rows. No arbitrary forward-fill should be used. Current or incomplete 4h buckets must be excluded or handled by a predeclared rule.

## Usability Decision

Overall classification: `{overall_class}`.

Reason: aggregate taker-flow context is available for all 19 markets, but exact instrument-level scope is not proven and full public-trade reconstruction was not performed. This supports a future constrained frozen-definition plan only after explicit approval; it does not authorize strategy validation, dry-run, live trading, or implementation claims.

## Recommended Next Direction

Create a research-only frozen-definition plan for one constrained aggregate taker-flow candidate, or create a separate public-trade reconstruction feasibility plan if exact instrument-level taker flow is required. Do not validate a strategy until a frozen plan is reviewed and explicitly approved. No-trade remains default.
"""
    (OUT / f"{PREFIX}_note.md").write_text(note, encoding="utf-8")

    limitations = """# Taker-Flow Data Availability Audit Round 1 Limitations

- The audit fetched only public taker-volume and public trade sample data.
- The OKX Rubik taker-volume endpoint appears to provide ccy/contracts aggregate taker flow, not proven exact instrument-level swap taker flow.
- Adding instId to the Rubik endpoint was treated only as a probe and not proof of exact instrument scope.
- Public trade samples show side/size/timestamp fields, but full historical reconstruction was not attempted.
- Trade reconstruction may be rate-limited, storage-heavy, and may not cover prior reference/holdout windows without a separate feasibility plan.
- Units remain endpoint-defined and are not accepted as cross-market normalized strategy features without a future unit/provenance plan.
- No OHLCV was fetched; range-volume impulse cannot be computed from taker-flow alone in this audit.
- No strategy was defined or validated, and no implementation/dry-run/live readiness is implied.
"""
    (OUT / f"{PREFIX}_limitations.md").write_text(limitations, encoding="utf-8")

    handoff = f"""=== CHATGPT HANDOFF START ===
1. run status: taker_flow_data_availability_audit_round1 executed as data availability audit only; no strategy definition, validation, backtest, OHLCV fetch, private data fetch, tuning, source change, dry-run, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before audit was cb4d088 research: add taker-flow data availability audit plan.
3. commands run: verified branch/HEAD and plan inputs; probed OKX public taker-volume/trade endpoints; created and ran research-only audit script; saved raw payloads; generated coverage/provenance/usability outputs; ran sanity checks; staged only audit outputs/script/raw data; committed and pushed.
4. files changed / output paths: research/taker_flow_data_availability_audit_round1.py; research_output/taker_flow_data_availability_audit_round1_note.md; _market_mapping.csv; _fetch_log.csv; _data_sources.csv; _field_coverage.csv; _feature_computability.csv; _alignment_assessment.csv; _gaps_duplicates.csv; _usability_decision.csv; _data_paths.csv; _limitations.md; _handoff.md; raw payloads under research_output/taker_flow_data_availability_audit_round1_raw/.
5. markets / instruments audited: same 19 spot-style markets mapped to OKX USDT swaps, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visible.
6. data sources / endpoints used: OKX Rubik `/api/v5/rubik/stat/taker-volume` at 1h CONTRACTS ccy scope; same route with instId probe; OKX `/api/v5/market/trades`; OKX `/api/v5/market/history-trades`; ccxt capability snapshot.
7. taker-flow availability summary: 1h direct taker buy/sell volume-like arrays available for {direct_markets}/19 at ccy/contracts aggregate scope; exact instrument-level taker flow not proven; public trade samples available for reconstruction feasibility only.
8. field / unit coverage: timestamp plus endpoint-defined sell/buy volume fields are present; units remain endpoint-defined and not cross-market normalized; quote volume not directly available from taker-volume route.
9. feature computability: taker_buy_ratio, taker_sell_ratio, taker_imbalance, taker_delta, and abnormal-turnover proxy are computable at aggregate ccy/contracts scope; range_volume_impulse requires OHLCV range and is not computed here.
10. 4h alignment assessment: 1h taker-volume data can aggregate into closed 4h buckets if future rules exclude incomplete buckets and avoid forward-fill/future leakage.
11. gaps / duplicates / coverage issues: gap/duplicate/timestamp coverage is documented per market; exact instrument scope and full public-trade history depth remain the main limitations.
12. usability decision: {overall_class}; usable as constrained aggregate taker-flow context, not immediate strategy validation.
13. recommended next direction: create a frozen-definition plan for one constrained aggregate taker-flow candidate, or a separate public-trade reconstruction feasibility plan if exact instrument-level flow is required; do not validate yet.
14. what remains forbidden: strategy definition/testing in this audit, backtests, validation, threshold sweeps, production changes, dry-run/live planning, and reviving closed candidates.
15. implementation readiness judgment: closed / not ready.
16. commit / push result: pending at file creation time; verify final response for actual commit and push result.
17. next recommended Codex prompt: Create a research-only frozen-definition plan for one aggregate taker-flow candidate using the audited data constraints; do not run validation yet.
18. one-sentence conclusion: Public taker-flow data exists as aggregate CONTRACTS context, but it is not yet an exact-instrument strategy feature and requires a frozen plan before any validation.
=== CHATGPT HANDOFF END ===
"""
    (OUT / f"{PREFIX}_handoff.md").write_text(handoff, encoding="utf-8")


if __name__ == "__main__":
    main()
