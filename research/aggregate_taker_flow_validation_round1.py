#!/usr/bin/env python3
"""Research-only aggregate taker-flow validation round 1.

Validates the frozen aggregate_taker_flow_exhaustion_reversal_round1 plan
against existing local OHLCV and audited OKX Rubik CONTRACTS ccy aggregate
1h taker buy/sell-like data. This script does not fetch data, change
production code, or define implementation readiness.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_output"
PREFIX = "aggregate_taker_flow_validation_round1"
RAW_TAKER_PATH = OUT / "taker_flow_data_availability_audit_round1_raw" / "okx_rubik_contracts_taker_volume_1h_by_ccy.jsonl"
FETCHED_OHLCV_PATH = OUT / "candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv"

MARKETS = [
    "AAVEUSDT",
    "ADAUSDT",
    "ATOMUSDT",
    "AVAXUSDT",
    "BCHUSDT",
    "BNBUSDT",
    "BTCUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "ETCUSDT",
    "ETHUSDT",
    "FILUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "NEARUSDT",
    "SOLUSDT",
    "TRXUSDT",
    "UNIUSDT",
    "XRPUSDT",
]

FAMILY_BY_MARKET = {
    "BTCUSDT": "majors",
    "ETHUSDT": "majors",
    "SOLUSDT": "large_alts",
    "BNBUSDT": "large_alts",
    "XRPUSDT": "large_alts",
    "ADAUSDT": "large_alts",
    "AVAXUSDT": "large_alts",
    "LINKUSDT": "large_alts",
    "UNIUSDT": "defi",
    "AAVEUSDT": "defi",
    "DOGEUSDT": "meme_high_beta",
}

STARTING_EQUITY = 100_000.0
FIXED_NOTIONAL = 1_000.0
FEE_RATE = 0.0005
EXTRA_SLIPPAGE_BPS = [0.0, 2.5, 5.0, 10.0]
SELL_IMBALANCE_THRESHOLD = 0.20
TAKER_SCOPE_LABEL = "aggregate_ccy_contracts_context_not_exact_instrument_flow"


@dataclass
class TakerState:
    allowed: bool
    reason: str
    bucket: str
    bucket_start: str
    bucket_end: str
    row_count: int
    buy_volume: float | None
    sell_volume: float | None
    total_volume: float | None
    taker_imbalance: float | None
    sell_imbalance: float | None
    used_future_rows: bool


def family(market: str) -> str:
    return FAMILY_BY_MARKET.get(market, "other")


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def simple_rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0).rolling(length).mean()
    loss = (-delta.clip(upper=0.0)).rolling(length).mean()
    rs = gain / loss.replace(0.0, np.nan)
    return 100 - (100 / (1 + rs))


def prepare_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy().sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    for column in ["open", "high", "low", "close", "volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["ema20"] = ema(df["close"], 20)
    df["atr14"] = true_range(df["high"], df["low"], df["close"]).rolling(14).mean()
    df["rsi14"] = simple_rsi(df["close"], 14)
    df["prev_close"] = df["close"].shift(1)
    df["recent_low10"] = df["low"].rolling(10).min()
    df["entry_signal"] = (df["rsi14"] <= 30) & (df["close"] < df["ema20"]) & (df["close"] > df["prev_close"])
    return df.reset_index(drop=True)


def parse_taker_rows(data: Any) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if not isinstance(data, list):
        return pd.DataFrame(columns=["timestamp", "sell_volume", "buy_volume"])
    for item in data:
        if not isinstance(item, list) or len(item) < 3:
            continue
        try:
            timestamp = pd.to_datetime(int(float(item[0])), unit="ms", utc=True)
            sell_volume = float(item[1])
            buy_volume = float(item[2])
        except Exception:
            continue
        rows.append({"timestamp": timestamp, "sell_volume": sell_volume, "buy_volume": buy_volume})
    if not rows:
        return pd.DataFrame(columns=["timestamp", "sell_volume", "buy_volume"])
    df = pd.DataFrame(rows).sort_values("timestamp").drop_duplicates("timestamp", keep="last").reset_index(drop=True)
    return df


def load_taker_data() -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    with RAW_TAKER_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            market = record.get("market")
            if market not in MARKETS:
                continue
            result[market] = parse_taker_rows(record.get("payload", {}).get("data"))
    return result


def taker_bucket_name(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "missing_or_incomplete"
    if value < -0.20:
        return "sell_imbalance_lt_minus_0_20"
    if value < 0.0:
        return "sell_imbalance_minus_0_20_to_0"
    if value < SELL_IMBALANCE_THRESHOLD:
        return "sell_imbalance_0_to_0_20"
    if value < 0.40:
        return "sell_imbalance_0_20_to_0_40"
    return "sell_imbalance_gte_0_40"


def taker_state(taker: pd.DataFrame, candle_time: pd.Timestamp) -> TakerState:
    start = pd.Timestamp(candle_time)
    end = start + pd.Timedelta(hours=4)
    base = {
        "bucket_start": start.isoformat(),
        "bucket_end": end.isoformat(),
        "buy_volume": None,
        "sell_volume": None,
        "total_volume": None,
        "taker_imbalance": None,
        "sell_imbalance": None,
        "used_future_rows": False,
    }
    if taker.empty:
        return TakerState(False, "missing_taker_flow", "missing_or_incomplete", row_count=0, **base)
    bucket = taker[(taker["timestamp"] >= start) & (taker["timestamp"] < end)].copy()
    row_count = int(bucket["timestamp"].nunique()) if not bucket.empty else 0
    if row_count == 0:
        return TakerState(False, "missing_taker_flow", "missing_or_incomplete", row_count=0, **base)
    used_future_rows = bool((bucket["timestamp"] >= end).any())
    if row_count < 4:
        base["used_future_rows"] = used_future_rows
        return TakerState(False, "incomplete_4h_bucket", "missing_or_incomplete", row_count=row_count, **base)
    buy = float(bucket["buy_volume"].sum())
    sell = float(bucket["sell_volume"].sum())
    total = buy + sell
    if not math.isfinite(total) or total <= 0:
        return TakerState(
            False,
            "total_volume_lte_0",
            "missing_or_incomplete",
            row_count=row_count,
            buy_volume=buy,
            sell_volume=sell,
            total_volume=total,
            taker_imbalance=None,
            sell_imbalance=None,
            bucket_start=start.isoformat(),
            bucket_end=end.isoformat(),
            used_future_rows=used_future_rows,
        )
    taker_imbalance = (buy - sell) / total
    sell_imbalance = (sell - buy) / total
    allowed = sell_imbalance >= SELL_IMBALANCE_THRESHOLD
    reason = "allowed_sell_imbalance_ge_0_20" if allowed else "sell_imbalance_below_0_20"
    return TakerState(
        allowed,
        reason,
        taker_bucket_name(sell_imbalance),
        start.isoformat(),
        end.isoformat(),
        row_count,
        buy,
        sell,
        total,
        taker_imbalance,
        sell_imbalance,
        used_future_rows,
    )


def exit_position(row: pd.Series, pos: dict[str, Any], index: int) -> tuple[str, float] | None:
    if float(row["low"]) <= pos["stop_price"]:
        return "stop_loss", pos["stop_price"]
    hit_target = float(row["high"]) >= pos["target_price"]
    hit_ema20 = float(row["high"]) >= float(row["ema20"])
    if hit_target and hit_ema20:
        if float(row["ema20"]) <= pos["target_price"]:
            return "EMA20_touch", float(row["ema20"])
        return "take_profit", pos["target_price"]
    if hit_target:
        return "take_profit", pos["target_price"]
    if hit_ema20:
        return "EMA20_touch", float(row["ema20"])
    if index - pos["entry_index"] >= 8:
        return "time_stop_8_bars", float(row["close"])
    return None


def simulate_market(
    market: str,
    data: pd.DataFrame,
    validation_start: pd.Timestamp,
    validation_end: pd.Timestamp,
    taker: pd.DataFrame,
    use_gate: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    trades: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    pos: dict[str, Any] | None = None
    counts = {
        "signals_all": 0,
        "entry_candidates": 0,
        "invalid_candidates": 0,
        "signals_while_position_or_exit": 0,
        "coverage_checks": 0,
        "complete_taker_buckets": 0,
        "missing_or_incomplete_buckets": 0,
    }
    candidate = "aggregate_taker_flow_exhaustion_reversal_round1" if use_gate else "ungated_oversold_reversal_base_stream_round1"

    for index, row in data.iterrows():
        timestamp = pd.Timestamp(row["timestamp"])
        in_window = validation_start <= timestamp <= validation_end
        exited_this_bar = False

        if pos is not None and in_window:
            exit_data = exit_position(row, pos, index)
            if exit_data is not None:
                exit_reason, exit_price = exit_data
                size = pos["size"]
                commission = (pos["entry_price"] + exit_price) * size * FEE_RATE
                gross_pnl = (exit_price - pos["entry_price"]) * size
                pnl = gross_pnl - commission
                trades.append(
                    {
                        "candidate": candidate,
                        "scope": "later_fetched",
                        "taker_flow_scope": TAKER_SCOPE_LABEL,
                        "market": market,
                        "family": family(market),
                        "entry_timestamp": pos["entry_timestamp"].isoformat(),
                        "exit_timestamp": timestamp.isoformat(),
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "stop_price": pos["stop_price"],
                        "target_price": pos["target_price"],
                        "exit_reason": exit_reason,
                        "hold_bars": index - pos["entry_index"],
                        "pnl": pnl,
                        "gross_pnl": gross_pnl,
                        "commission": commission,
                        "entry_taker_reason": pos["taker_reason"],
                        "entry_taker_bucket": pos["taker_bucket"],
                        "entry_sell_imbalance_4h": pos["sell_imbalance"],
                        "entry_taker_buy_volume_4h": pos["buy_volume"],
                        "entry_taker_sell_volume_4h": pos["sell_volume"],
                        "entry_total_taker_volume_4h": pos["total_volume"],
                        "entry_taker_bucket_start": pos["bucket_start"],
                        "entry_taker_bucket_end": pos["bucket_end"],
                        "entry_taker_row_count": pos["row_count"],
                    }
                )
                pos = None
                exited_this_bar = True

        if in_window and bool(row["entry_signal"]):
            counts["signals_all"] += 1
            if pos is not None or exited_this_bar:
                counts["signals_while_position_or_exit"] += 1
                continue

            entry_price = float(row["close"])
            stop_price = float(row["recent_low10"]) - 0.5 * float(row["atr14"])
            risk = entry_price - stop_price
            if not math.isfinite(risk) or risk <= 0:
                counts["invalid_candidates"] += 1
                continue

            counts["entry_candidates"] += 1
            counts["coverage_checks"] += 1
            state = taker_state(taker, timestamp)
            if state.row_count >= 4 and state.total_volume is not None and state.total_volume > 0:
                counts["complete_taker_buckets"] += 1
            else:
                counts["missing_or_incomplete_buckets"] += 1

            if use_gate and not state.allowed:
                blocked.append(
                    {
                        "candidate": candidate,
                        "scope": "later_fetched",
                        "taker_flow_scope": TAKER_SCOPE_LABEL,
                        "market": market,
                        "family": family(market),
                        "entry_timestamp": timestamp.isoformat(),
                        "entry_price": entry_price,
                        "blocked_reason": state.reason,
                        "taker_bucket": state.bucket,
                        "bucket_start": state.bucket_start,
                        "bucket_end": state.bucket_end,
                        "taker_row_count": state.row_count,
                        "taker_buy_volume_4h": state.buy_volume,
                        "taker_sell_volume_4h": state.sell_volume,
                        "total_taker_volume_4h": state.total_volume,
                        "taker_imbalance_4h": state.taker_imbalance,
                        "sell_imbalance_4h": state.sell_imbalance,
                        "used_future_rows": state.used_future_rows,
                    }
                )
                continue

            size = FIXED_NOTIONAL / entry_price
            pos = {
                "entry_index": index,
                "entry_timestamp": timestamp,
                "entry_price": entry_price,
                "stop_price": stop_price,
                "target_price": entry_price + 1.5 * risk,
                "size": size,
                "taker_reason": state.reason,
                "taker_bucket": state.bucket,
                "sell_imbalance": state.sell_imbalance,
                "buy_volume": state.buy_volume,
                "sell_volume": state.sell_volume,
                "total_volume": state.total_volume,
                "bucket_start": state.bucket_start,
                "bucket_end": state.bucket_end,
                "row_count": state.row_count,
            }

    return trades, blocked, counts


def profit_factor(trades: list[dict[str, Any]]) -> float | None:
    wins = sum(float(t["pnl"]) for t in trades if float(t["pnl"]) > 0)
    losses = abs(sum(float(t["pnl"]) for t in trades if float(t["pnl"]) < 0))
    if losses > 0:
        return wins / losses
    if wins > 0:
        return math.inf
    return None


def max_drawdown_pct(trades: list[dict[str, Any]]) -> float:
    if not trades:
        return 0.0
    ordered = sorted(trades, key=lambda item: (item["exit_timestamp"], item["market"]))
    equity = STARTING_EQUITY
    peak = equity
    max_dd = 0.0
    for trade in ordered:
        equity += float(trade["pnl"])
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1.0)
    return abs(max_dd) * 100


def trade_metrics(trades: list[dict[str, Any]]) -> dict[str, Any]:
    pnls = [float(t["pnl"]) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    holds = [int(t["hold_bars"]) for t in trades]
    exit_reasons = {reason: sum(1 for t in trades if t.get("exit_reason") == reason) for reason in ["EMA20_touch", "take_profit", "stop_loss", "time_stop_8_bars"]}
    return {
        "total_trades": len(trades),
        "net_pnl": sum(pnls),
        "profit_factor": profit_factor(trades),
        "max_drawdown_pct": max_drawdown_pct(trades),
        "win_rate": len(wins) / len(trades) * 100 if trades else 0.0,
        "avg_trade": float(np.mean(pnls)) if pnls else None,
        "median_trade": float(np.median(pnls)) if pnls else None,
        "gross_profit": sum(wins),
        "gross_loss": abs(sum(losses)),
        "commission": sum(float(t["commission"]) for t in trades),
        "avg_hold_bars": float(np.mean(holds)) if holds else None,
        "median_hold_bars": float(np.median(holds)) if holds else None,
        **exit_reasons,
    }


def rows_for_group(candidate: str, trades: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    rows = []
    if group_key == "market":
        groups = MARKETS
    else:
        groups = sorted(set(FAMILY_BY_MARKET.values()) | {"other"})
    for group in groups:
        subset = [t for t in trades if t[group_key] == group]
        metrics = trade_metrics(subset)
        rows.append(
            {
                "candidate": candidate,
                "scope": "later_fetched",
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "market": group if group_key == "market" else "",
                "family": family(group) if group_key == "market" else group,
                **metrics,
            }
        )
    return rows


def write_csv(name: str, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path = OUT / f"{PREFIX}_{name}.csv"
    if fields is None:
        field_set: list[str] = []
        for row in rows:
            for key in row:
                if key not in field_set:
                    field_set.append(key)
        fields = field_set or ["note"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)):
        if math.isinf(float(value)):
            return "inf"
        return f"{float(value):.6f}"
    return str(value)


def concentration(candidate: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    market_pnl = sorted(
        [(m, sum(float(t["pnl"]) for t in trades if t["market"] == m)) for m in MARKETS],
        key=lambda pair: pair[1],
        reverse=True,
    )
    positive = [(m, v) for m, v in market_pnl if v > 0]
    positive_sum = sum(v for _, v in positive)
    net = sum(v for _, v in market_pnl)
    top3 = positive[:3]
    top5 = positive[:5]
    trade_pos = sorted([float(t["pnl"]) for t in trades if float(t["pnl"]) > 0], reverse=True)
    top10 = sum(trade_pos[:10])
    return {
        "candidate": candidate,
        "scope": "later_fetched",
        "taker_flow_scope": TAKER_SCOPE_LABEL,
        "aggregate_net_pnl": net,
        "positive_market_pnl_sum": positive_sum,
        "top3_markets": "|".join(m for m, _ in top3),
        "top3_pnl": sum(v for _, v in top3),
        "top3_pct_of_positive_market_pnl": (sum(v for _, v in top3) / positive_sum * 100) if positive_sum else None,
        "top5_markets": "|".join(m for m, _ in top5),
        "top5_pnl": sum(v for _, v in top5),
        "top5_pct_of_positive_market_pnl": (sum(v for _, v in top5) / positive_sum * 100) if positive_sum else None,
        "top10_positive_trade_pnl": top10,
        "top10_positive_trade_pct_of_positive_trade_pnl": (top10 / sum(trade_pos) * 100) if trade_pos else None,
        "interpretation": "aggregate_not_positive_concentration_not_rescuing" if net <= 0 else "check_top_concentration",
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    taker_by_market = load_taker_data()
    fetched = pd.read_csv(FETCHED_OHLCV_PATH)
    fetched["timestamp"] = pd.to_datetime(fetched["timestamp"], utc=True)

    all_base: list[dict[str, Any]] = []
    all_gated: list[dict[str, Any]] = []
    all_blocked: list[dict[str, Any]] = []
    data_coverage: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    count_by_market: dict[str, dict[str, int]] = {}

    for market in MARKETS:
        local = pd.read_csv(ROOT / "data" / f"{market}_4h.csv")
        local["timestamp"] = pd.to_datetime(local["timestamp"], utc=True)
        local["source"] = "local_warmup"
        market_fetched = fetched[fetched["market"] == market].copy()
        market_fetched["source"] = "later_fetched"
        combined = pd.concat(
            [
                local[["timestamp", "open", "high", "low", "close", "volume", "source"]],
                market_fetched[["timestamp", "open", "high", "low", "close", "volume", "source"]],
            ],
            ignore_index=True,
        )
        combined = combined.sort_values("timestamp").drop_duplicates("timestamp", keep="last").reset_index(drop=True)
        prepared = prepare_ohlcv(combined)
        validation_start = market_fetched["timestamp"].min()
        validation_end = market_fetched["timestamp"].max()
        taker = taker_by_market.get(market, pd.DataFrame(columns=["timestamp", "sell_volume", "buy_volume"]))

        base_trades, _base_blocked, base_counts = simulate_market(market, prepared, validation_start, validation_end, taker, use_gate=False)
        gated_trades, blocked, gated_counts = simulate_market(market, prepared, validation_start, validation_end, taker, use_gate=True)
        all_base.extend(base_trades)
        all_gated.extend(gated_trades)
        all_blocked.extend(blocked)

        count_by_market[market] = {
            "base_signals_all": base_counts["signals_all"],
            "base_entry_candidates": base_counts["entry_candidates"],
            "base_signals_while_position_or_exit": base_counts["signals_while_position_or_exit"],
            "base_invalid_candidates": base_counts["invalid_candidates"],
            "gated_signals_all": gated_counts["signals_all"],
            "gated_entry_candidates": gated_counts["entry_candidates"],
            "gated_signals_while_position_or_exit": gated_counts["signals_while_position_or_exit"],
            "gated_invalid_candidates": gated_counts["invalid_candidates"],
            "blocked_entries": len(blocked),
            "complete_taker_buckets_checked": gated_counts["complete_taker_buckets"],
            "missing_or_incomplete_buckets_checked": gated_counts["missing_or_incomplete_buckets"],
        }

        taker_start = taker["timestamp"].min().isoformat() if not taker.empty else ""
        taker_end = taker["timestamp"].max().isoformat() if not taker.empty else ""
        taker_dupes = int(len(taker) - taker["timestamp"].nunique()) if not taker.empty else 0
        taker_gaps = 0
        if len(taker) > 1:
            deltas = taker["timestamp"].sort_values().diff().dropna().dt.total_seconds() / 3600
            taker_gaps = int((deltas > 1.0).sum())
        data_coverage.append(
            {
                "market": market,
                "family": family(market),
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "ohlcv_source": "local_4h_warmup_plus_candidate_d_later_fetched_ohlcv",
                "validation_start": validation_start.isoformat(),
                "validation_end": validation_end.isoformat(),
                "later_fetched_candles": len(market_fetched),
                "taker_source": "research_output/taker_flow_data_availability_audit_round1_raw/okx_rubik_contracts_taker_volume_1h_by_ccy.jsonl",
                "taker_rows_1h": len(taker),
                "taker_start": taker_start,
                "taker_end": taker_end,
                "taker_cadence": "1h",
                "duplicate_taker_timestamps": taker_dupes,
                "taker_gap_count_gt_1h": taker_gaps,
                "base_entry_candidates": base_counts["entry_candidates"],
                "gated_entry_candidates": gated_counts["entry_candidates"],
                "complete_taker_buckets_checked": gated_counts["complete_taker_buckets"],
                "missing_or_incomplete_buckets_checked": gated_counts["missing_or_incomplete_buckets"],
                "blocked_entries": len(blocked),
                "coverage_status": "usable_existing_audited_aggregate_context" if len(taker) else "missing_taker_flow",
            }
        )
        alignment_rows.append(
            {
                "market": market,
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "ohlcv_timestamp_convention": "4h candle open timestamp; signal evaluated at candle close",
                "taker_bucket_rule": "aggregate 1h taker rows with timestamp >= 4h open and < 4h open + 4h",
                "future_rows_used": False,
                "partial_4h_buckets_allowed": False,
                "forward_fill_used": False,
                "exact_instrument_claim": False,
                "complete_buckets_checked": gated_counts["complete_taker_buckets"],
                "missing_or_incomplete_buckets_checked": gated_counts["missing_or_incomplete_buckets"],
                "alignment_status": "passed_no_future_rows_no_forward_fill",
            }
        )

    base_map = {(t["market"], t["entry_timestamp"]): t for t in all_base}
    for item in all_blocked:
        base_trade = base_map.get((item["market"], item["entry_timestamp"]))
        item["base_trade_pnl_if_taken"] = base_trade["pnl"] if base_trade else ""
        item["blocked_outcome"] = (
            "avoided_loser" if base_trade and base_trade["pnl"] < 0 else "missed_winner" if base_trade and base_trade["pnl"] > 0 else "no_matching_base_trade"
        )

    base_metrics = trade_metrics(all_base)
    gated_metrics = trade_metrics(all_gated)
    candidates = [
        ("ungated_oversold_reversal_base_stream_round1", all_base, base_metrics),
        ("aggregate_taker_flow_exhaustion_reversal_round1", all_gated, gated_metrics),
    ]

    aggregate_rows: list[dict[str, Any]] = []
    for candidate, trades, metrics in candidates:
        positive_markets = sum(1 for m in MARKETS if sum(float(t["pnl"]) for t in trades if t["market"] == m) > 0)
        negative_markets = sum(1 for m in MARKETS if sum(float(t["pnl"]) for t in trades if t["market"] == m) < 0)
        aggregate_rows.append(
            {
                "candidate": candidate,
                "scope": "later_fetched",
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "market_count": len(MARKETS),
                **metrics,
                "positive_markets": positive_markets,
                "negative_markets": negative_markets,
                "flat_markets": len(MARKETS) - positive_markets - negative_markets,
                "base_entry_candidates": sum(v["base_entry_candidates"] for v in count_by_market.values()),
                "gated_entry_candidates": sum(v["gated_entry_candidates"] for v in count_by_market.values()),
                "blocked_entries": len(all_blocked) if candidate == "aggregate_taker_flow_exhaustion_reversal_round1" else 0,
            }
        )

    market_rows = rows_for_group("ungated_oversold_reversal_base_stream_round1", all_base, "market") + rows_for_group(
        "aggregate_taker_flow_exhaustion_reversal_round1", all_gated, "market"
    )
    for row in market_rows:
        row.update(count_by_market.get(row["market"], {}))
    family_rows = rows_for_group("ungated_oversold_reversal_base_stream_round1", all_base, "family") + rows_for_group(
        "aggregate_taker_flow_exhaustion_reversal_round1", all_gated, "family"
    )

    reason_rows = []
    for reason in ["missing_taker_flow", "incomplete_4h_bucket", "total_volume_lte_0", "sell_imbalance_below_0_20"]:
        subset = [b for b in all_blocked if b["blocked_reason"] == reason]
        known = [float(b["base_trade_pnl_if_taken"]) for b in subset if b["base_trade_pnl_if_taken"] != ""]
        reason_rows.append(
            {
                "blocked_reason": reason,
                "blocked_entries": len(subset),
                "matched_base_trades": len(known),
                "avoided_losers": sum(1 for v in known if v < 0),
                "missed_winners": sum(1 for v in known if v > 0),
                "net_base_pnl_blocked": sum(known) if known else 0.0,
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "interpretation": "positive_if_blocked_base_pnl_was_negative" if sum(known) < 0 else "blocked_winners_or_no_effect",
            }
        )

    bucket_rows: list[dict[str, Any]] = []
    bucket_names = [
        "missing_or_incomplete",
        "sell_imbalance_lt_minus_0_20",
        "sell_imbalance_minus_0_20_to_0",
        "sell_imbalance_0_to_0_20",
        "sell_imbalance_0_20_to_0_40",
        "sell_imbalance_gte_0_40",
    ]
    for candidate, trades, _metrics in candidates:
        for bucket in bucket_names:
            subset = [t for t in trades if t.get("entry_taker_bucket") == bucket]
            bucket_metrics = trade_metrics(subset)
            bucket_rows.append(
                {
                    "candidate": candidate,
                    "scope": "later_fetched",
                    "taker_flow_scope": TAKER_SCOPE_LABEL,
                    "sell_imbalance_bucket": bucket,
                    **bucket_metrics,
                }
            )

    blocked_known = [b for b in all_blocked if b["base_trade_pnl_if_taken"] != ""]
    missed_avoided_rows = [
        {
            "candidate": "aggregate_taker_flow_exhaustion_reversal_round1",
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "blocked_entries": len(all_blocked),
            "matched_base_trades": len(blocked_known),
            "avoided_losers": sum(1 for b in blocked_known if float(b["base_trade_pnl_if_taken"]) < 0),
            "avoided_loser_pnl_sum": sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known if float(b["base_trade_pnl_if_taken"]) < 0),
            "missed_winners": sum(1 for b in blocked_known if float(b["base_trade_pnl_if_taken"]) > 0),
            "missed_winner_pnl_sum": sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known if float(b["base_trade_pnl_if_taken"]) > 0),
            "net_base_pnl_blocked": sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known),
            "gated_minus_base_net_pnl": gated_metrics["net_pnl"] - base_metrics["net_pnl"],
            "interpretation": "improvement_must_be_positive_edge_not_only_trade_reduction",
        }
    ]

    btc_rows = []
    for candidate, trades, _metrics in candidates:
        subset = [t for t in trades if t["market"] == "BTCUSDT"]
        metrics = trade_metrics(subset)
        btc_rows.append(
            {
                "candidate": candidate,
                "scope": "later_fetched",
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "market": "BTCUSDT",
                **metrics,
                "assessment": "non_negative_or_no_trade" if metrics["net_pnl"] >= 0 else "negative_btc_result",
            }
        )

    weak_rows = []
    for candidate, trades, _metrics in candidates:
        for market in ["DOGEUSDT", "DOTUSDT", "UNIUSDT"]:
            subset = [t for t in trades if t["market"] == market]
            metrics = trade_metrics(subset)
            weak_rows.append({"candidate": candidate, "scope": "later_fetched", "taker_flow_scope": TAKER_SCOPE_LABEL, "market": market, "family": family(market), **metrics})

    concentration_rows = [concentration(candidate, trades) for candidate, trades, _metrics in candidates]

    no_trade_rows = [
        {
            "candidate": candidate,
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "candidate_net_pnl": metrics["net_pnl"],
            "no_trade_net_pnl": 0.0,
            "candidate_minus_no_trade": metrics["net_pnl"],
            "interpretation": "beats_no_trade" if metrics["net_pnl"] > 0 else "no_trade_preferred",
        }
        for candidate, _trades, metrics in candidates
    ]

    btc_fetched = fetched[fetched["market"] == "BTCUSDT"].sort_values("timestamp")
    first_close = float(btc_fetched.iloc[0]["close"])
    last_close = float(btc_fetched.iloc[-1]["close"])
    btc_norm_pnl = (last_close / first_close - 1) * STARTING_EQUITY
    btc_close = btc_fetched["close"].astype(float)
    btc_dd = abs((btc_close / btc_close.cummax() - 1).min()) * 100
    buy_hold_rows = [
        {
            "candidate": candidate,
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "first_close": first_close,
            "last_close": last_close,
            "normalized_notional": STARTING_EQUITY,
            "passive_btc_normalized_pnl": btc_norm_pnl,
            "passive_btc_return_pct": btc_norm_pnl / STARTING_EQUITY * 100,
            "passive_btc_max_close_to_close_dd_pct": btc_dd,
            "candidate_net_pnl": metrics["net_pnl"],
            "candidate_minus_passive_btc": metrics["net_pnl"] - btc_norm_pnl,
            "interpretation": "passive_btc_opportunity_cost_only",
        }
        for candidate, _trades, metrics in candidates
    ]

    base_comparison_rows = [
        {
            "candidate": "aggregate_taker_flow_exhaustion_reversal_round1",
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "base_net_pnl": base_metrics["net_pnl"],
            "gated_net_pnl": gated_metrics["net_pnl"],
            "gated_minus_base_net_pnl": gated_metrics["net_pnl"] - base_metrics["net_pnl"],
            "base_profit_factor": base_metrics["profit_factor"],
            "gated_profit_factor": gated_metrics["profit_factor"],
            "profit_factor_delta": (gated_metrics["profit_factor"] or 0) - (base_metrics["profit_factor"] or 0),
            "base_trades": base_metrics["total_trades"],
            "gated_trades": gated_metrics["total_trades"],
            "trade_reduction": base_metrics["total_trades"] - gated_metrics["total_trades"],
            "blocked_entries": len(all_blocked),
            "interpretation": "improved_but_still_negative" if gated_metrics["net_pnl"] > base_metrics["net_pnl"] and gated_metrics["net_pnl"] < 0 else "failed_or_not_improved",
        }
    ]

    candidate_d_later_net = -174.23466018511795
    candidate_d_later_pf = 0.13132609206323043
    candidate_d_rows = [
        {
            "candidate": "aggregate_taker_flow_exhaustion_reversal_round1",
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "candidate_d_later_failure_net_pnl": candidate_d_later_net,
            "candidate_d_later_failure_pf": candidate_d_later_pf,
            "gated_net_pnl": gated_metrics["net_pnl"],
            "gated_profit_factor": gated_metrics["profit_factor"],
            "net_pnl_delta_vs_candidate_d_later_failure": gated_metrics["net_pnl"] - candidate_d_later_net,
            "pf_delta_vs_candidate_d_later_failure": (gated_metrics["profit_factor"] or 0) - candidate_d_later_pf,
            "interpretation": "comparison_reference_only_candidate_d_not_revived",
        }
    ]

    autonomous_rows = [
        {
            "candidate": "aggregate_taker_flow_exhaustion_reversal_round1",
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "autonomous_loop_promoted_candidates": 0,
            "best_near_miss": "K_liquidation_wick_bounce",
            "best_near_miss_holdout_net_pnl": 769.166224,
            "best_near_miss_holdout_pf": 1.084287,
            "best_near_miss_later_data_net_pnl": -35.427328,
            "best_near_miss_later_data_pf": 0.0,
            "gated_net_pnl": gated_metrics["net_pnl"],
            "gated_profit_factor": gated_metrics["profit_factor"],
            "interpretation": "prior_autonomous_failures_are_context_only_not_promotion_benchmark",
        }
    ]

    slippage_rows = []
    for bps in EXTRA_SLIPPAGE_BPS:
        adjusted = []
        for trade in all_gated:
            extra = (trade["entry_price"] + trade["exit_price"]) * (FIXED_NOTIONAL / trade["entry_price"]) * (bps / 10000)
            copy = dict(trade)
            copy["pnl"] = trade["pnl"] - extra
            adjusted.append(copy)
        metrics = trade_metrics(adjusted)
        slippage_rows.append(
            {
                "candidate": "aggregate_taker_flow_exhaustion_reversal_round1",
                "scope": "later_fetched",
                "taker_flow_scope": TAKER_SCOPE_LABEL,
                "extra_slippage_bps_per_side": bps,
                "net_pnl_after_extra_slippage": metrics["net_pnl"],
                "profit_factor_after_extra_slippage": metrics["profit_factor"],
                "candidate_minus_no_trade": metrics["net_pnl"],
                "interpretation": "no_trade_preferred_under_sensitivity" if metrics["net_pnl"] <= 0 else "positive_under_sensitivity",
            }
        )

    decision_reasons: list[str] = []
    decision = "fail"
    if gated_metrics["net_pnl"] <= 0:
        decision_reasons.append("aggregate_not_positive")
        decision_reasons.append("no_trade_not_beaten")
    if (gated_metrics["profit_factor"] or 0) < 1.0:
        decision_reasons.append("profit_factor_below_1")
    if gated_metrics["net_pnl"] <= base_metrics["net_pnl"]:
        decision_reasons.append("worse_than_ungated_base_stream")
    btc_gated = trade_metrics([t for t in all_gated if t["market"] == "BTCUSDT"])
    if btc_gated["total_trades"] > 0 and btc_gated["net_pnl"] < 0:
        decision_reasons.append("BTCUSDT_negative_with_meaningful_trades")
    if gated_metrics["total_trades"] < 5:
        decision_reasons.append("low_trade_count")
    if len(all_blocked) and sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known) > 0:
        decision_reasons.append("gate_mainly_blocks_winners")
    if sum(v["complete_taker_buckets_checked"] for v in count_by_market.values()) == 0:
        decision_reasons.append("insufficient_taker_flow_coverage")
    decision_rows = [
        {
            "candidate": "aggregate_taker_flow_exhaustion_reversal_round1",
            "scope": "later_fetched",
            "taker_flow_scope": TAKER_SCOPE_LABEL,
            "decision": decision,
            "decision_reasons": ";".join(dict.fromkeys(decision_reasons)),
            "recommendation": "park_aggregate_taker_flow_round1_for_implementation_keep_no_trade_default",
            "implementation_readiness": "closed_not_ready",
            "dry_run_ready": False,
            "live_ready": False,
        }
    ]

    write_csv("data_coverage", data_coverage)
    write_csv("aggregate_metrics", aggregate_rows)
    write_csv("market_metrics", market_rows)
    write_csv("family_metrics", family_rows)
    write_csv("blocked_entries", all_blocked)
    write_csv("blocked_by_reason", reason_rows)
    write_csv("taker_flow_buckets", bucket_rows)
    write_csv("missed_winners_avoided_losers", missed_avoided_rows)
    write_csv("btcusdt_assessment", btc_rows)
    write_csv("weak_market_assessment", weak_rows)
    write_csv("concentration", concentration_rows)
    write_csv("no_trade_comparison", no_trade_rows)
    write_csv("buy_hold_comparison", buy_hold_rows)
    write_csv("base_stream_comparison", base_comparison_rows)
    write_csv("candidate_d_later_failure_comparison", candidate_d_rows)
    write_csv("autonomous_loop_comparison", autonomous_rows)
    write_csv("slippage_fee_sensitivity", slippage_rows)
    write_csv("alignment_audit", alignment_rows)
    write_csv("decision", decision_rows)

    note = f"""# Aggregate Taker-Flow Validation Round 1

## Scope
This was a research-only validation of `aggregate_taker_flow_exhaustion_reversal_round1` exactly according to `aggregate_taker_flow_validation_plan_round1`. No new data was fetched, no production source or parameter was changed, no threshold sweep was run, and no dry-run/live behavior was touched.

## Data Used
The validation used the same 19 approved markets. OHLCV came from local 4h files for indicator warmup plus `candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv` for the later-data validation window. Taker-flow came only from `taker_flow_data_availability_audit_round1_raw/okx_rubik_contracts_taker_volume_1h_by_ccy.jsonl`.

All taker-flow references are labeled as `{TAKER_SCOPE_LABEL}`. The OKX Rubik data is aggregate ccy/contracts context, not exact instrument-level taker flow.

## Frozen Rules
Base stream: RSI14 <= 30, close < EMA20, current close > previous close; stop at recent 10-candle low - 0.5 * ATR14; exits at EMA20 touch, 1.5R take profit, or 8 completed 4h bars; no add-ons or averaging down.

Gate: aggregate complete 1h taker rows into the closed 4h bucket for each candidate candle. Require total taker volume > 0 and sell_imbalance_4h >= 0.20. Missing, incomplete, or below-threshold buckets block entry. No forward-fill, no partial 4h buckets, and no future 1h rows are used.

## Key Result
Ungated base stream: {base_metrics['total_trades']} trades, net PnL {fmt(base_metrics['net_pnl'])}, PF {fmt(base_metrics['profit_factor'])}.

Aggregate taker-flow gated stream: {gated_metrics['total_trades']} trades, net PnL {fmt(gated_metrics['net_pnl'])}, PF {fmt(gated_metrics['profit_factor'])}, win rate {fmt(gated_metrics['win_rate'])}%, max DD {fmt(gated_metrics['max_drawdown_pct'])}%.

## Decision
Decision: {decision}. The candidate must remain research-only and not implementation-ready unless all predeclared gates are passed in a future separately approved plan.
"""
    (OUT / f"{PREFIX}_note.md").write_text(note, encoding="utf-8")

    limitations = f"""# Aggregate Taker-Flow Validation Round 1 Limitations

- Taker-flow data is `{TAKER_SCOPE_LABEL}`; it is not exact instrument-level taker flow.
- Validation used existing audited taker-flow raw data only; no new fetch was performed.
- The later-data OHLCV window is short for most non-BTC markets, so trade-count interpretation remains sample-limited.
- 1h taker rows were aggregated into closed 4h buckets; incomplete buckets were blocked, not filled.
- No arbitrary forward-fill or future 1h rows were used.
- Candidate D and autonomous loop failures are comparison references only and were not revived as implementation candidates.
- This validation does not authorize dry-run, live trading, implementation readiness, parameter tuning, threshold changes, or market removal.
"""
    (OUT / f"{PREFIX}_limitations.md").write_text(limitations, encoding="utf-8")

    handoff = f"""=== CHATGPT HANDOFF START ===
1. run status: aggregate_taker_flow_validation_round1 executed as research-only validation; no new data fetch, production source/parameter change, dry-run restart, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness; based on aggregate_taker_flow_validation_plan_round1.
3. commands run: loaded frozen plan inputs, local 4h OHLCV warmup, fetched later OHLCV, audited aggregate taker-flow raw data, simulated ungated and gated streams, wrote outputs.
4. files changed / output paths: research/aggregate_taker_flow_validation_round1.py plus research_output/aggregate_taker_flow_validation_round1_*.
5. validation data used: same 19 markets, local 4h warmup, candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv, audited OKX Rubik 1h CONTRACTS ccy aggregate taker data; BTCUSDT_1h excluded.
6. frozen base stream: RSI14 <= 30, close < EMA20, close > previous close, stop recent 10-candle low - 0.5*ATR14, exits at EMA20/1.5R/8 bars; no add-ons/averaging.
7. frozen aggregate taker-flow gate: closed 4h bucket from complete 1h aggregate ccy/contracts taker rows, sell_imbalance_4h >= 0.20, total volume > 0, missing/incomplete/below-threshold buckets block entry; no exact-instrument claim.
8. key gated results: {gated_metrics['total_trades']} trades, net PnL {fmt(gated_metrics['net_pnl'])}, PF {fmt(gated_metrics['profit_factor'])}, win rate {fmt(gated_metrics['win_rate'])}%, max DD {fmt(gated_metrics['max_drawdown_pct'])}%.
9. ungated base-stream comparison: base {base_metrics['total_trades']} trades, net PnL {fmt(base_metrics['net_pnl'])}, PF {fmt(base_metrics['profit_factor'])}; gated-minus-base net PnL {fmt(gated_metrics['net_pnl'] - base_metrics['net_pnl'])}.
10. blocked-entry result: {len(all_blocked)} blocked entries; matched blocked base PnL {fmt(sum(float(b['base_trade_pnl_if_taken']) for b in blocked_known))}; avoided losers {sum(1 for b in blocked_known if float(b['base_trade_pnl_if_taken']) < 0)}, missed winners {sum(1 for b in blocked_known if float(b['base_trade_pnl_if_taken']) > 0)}.
11. taker-flow bucket result: outputs report bucket performance in aggregate ccy/contracts context; below-threshold and missing/incomplete buckets were blocked.
12. BTCUSDT result: gated BTCUSDT net PnL {fmt(btc_gated['net_pnl'])}, PF {fmt(btc_gated['profit_factor'])}, trades {btc_gated['total_trades']}.
13. DOGE/DOT/UNI result: DOGE {fmt(sum(t['pnl'] for t in all_gated if t['market']=='DOGEUSDT'))}; DOT {fmt(sum(t['pnl'] for t in all_gated if t['market']=='DOTUSDT'))}; UNI {fmt(sum(t['pnl'] for t in all_gated if t['market']=='UNIUSDT'))}.
14. family-level result: majors {fmt(sum(t['pnl'] for t in all_gated if t['family']=='majors'))}; large_alts {fmt(sum(t['pnl'] for t in all_gated if t['family']=='large_alts'))}; defi {fmt(sum(t['pnl'] for t in all_gated if t['family']=='defi'))}; meme_high_beta {fmt(sum(t['pnl'] for t in all_gated if t['family']=='meme_high_beta'))}; other {fmt(sum(t['pnl'] for t in all_gated if t['family']=='other'))}.
15. no-trade comparison: no-trade interpretation is {'beats_no_trade' if gated_metrics['net_pnl'] > 0 else 'no_trade_preferred'} with candidate-minus-no-trade {fmt(gated_metrics['net_pnl'])}.
16. pass/caution/fail decision: {decision}.
17. what changed / did not change: changed only research outputs and research-only validation script; did not change production source, parameters, thresholds, base stream, deployment, PRs, dry-run, or live state.
18. implementation readiness judgment: closed_not_ready.
19. commit / push result: pending after output generation.
20. next recommended Codex prompt: Create a research-only postmortem for aggregate_taker_flow_validation_round1 and keep no-trade as default unless a future plan is explicitly approved.
21. one-sentence conclusion: Aggregate taker-flow validation remains research-only and no-trade stays default unless predeclared validation gates are met.
=== CHATGPT HANDOFF END ===
"""
    (OUT / f"{PREFIX}_handoff.md").write_text(handoff, encoding="utf-8")

    required = [
        "note.md",
        "data_coverage.csv",
        "aggregate_metrics.csv",
        "market_metrics.csv",
        "family_metrics.csv",
        "blocked_entries.csv",
        "blocked_by_reason.csv",
        "taker_flow_buckets.csv",
        "missed_winners_avoided_losers.csv",
        "btcusdt_assessment.csv",
        "weak_market_assessment.csv",
        "concentration.csv",
        "no_trade_comparison.csv",
        "buy_hold_comparison.csv",
        "base_stream_comparison.csv",
        "candidate_d_later_failure_comparison.csv",
        "autonomous_loop_comparison.csv",
        "slippage_fee_sensitivity.csv",
        "alignment_audit.csv",
        "decision.csv",
        "limitations.md",
        "handoff.md",
    ]
    missing = [name for name in required if not (OUT / f"{PREFIX}_{name}").exists()]
    if missing:
        raise RuntimeError(f"missing outputs: {missing}")

    print(f"base_net_pnl={base_metrics['net_pnl']:.8f} base_pf={(base_metrics['profit_factor'] or 0):.8f} base_trades={base_metrics['total_trades']}")
    print(f"gated_net_pnl={gated_metrics['net_pnl']:.8f} gated_pf={(gated_metrics['profit_factor'] or 0):.8f} gated_trades={gated_metrics['total_trades']}")
    print(f"blocked_entries={len(all_blocked)} decision={decision} taker_scope={TAKER_SCOPE_LABEL}")


if __name__ == "__main__":
    main()
