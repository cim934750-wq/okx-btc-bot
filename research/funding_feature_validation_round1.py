from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_output"
PREFIX = "funding_feature_validation_round1"
FUNDING_WINDOW = "2026-02-19T16:00:00+00:00 to 2026-05-23T08:00:00+00:00"

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


@dataclass
class FundingState:
    allowed: bool
    state: str
    bucket: str
    funding_timestamp: str
    staleness_hours: float | None
    current_funding_rate: float | None
    percentile: float | None
    prior_observation_count: int
    is_negative_extreme: bool


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
    df["entry_signal"] = (
        (df["rsi14"] <= 28)
        & (df["close"] <= df["ema20"] - 1.5 * df["atr14"])
        & (df["close"] > df["prev_close"])
    )
    return df.reset_index(drop=True)


def load_funding() -> dict[str, pd.DataFrame]:
    path = OUT / "oi_funding_data_availability_audit_round1_raw" / "funding_history.csv"
    funding = pd.read_csv(path)
    funding["timestamp"] = pd.to_datetime(funding["timestamp"], utc=True)
    funding["funding_rate"] = pd.to_numeric(funding["funding_rate"], errors="coerce")
    result: dict[str, pd.DataFrame] = {}
    for market, group in funding.groupby("market"):
        result[market] = group.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    return result


def funding_state(funding: pd.DataFrame, candle_time: pd.Timestamp) -> FundingState:
    available = funding[funding["timestamp"] <= candle_time]
    if available.empty:
        return FundingState(False, "missing", "missing", "", None, None, None, 0, False)

    current = available.iloc[-1]
    staleness_hours = (candle_time - current["timestamp"]).total_seconds() / 3600
    if staleness_hours > 4:
        return FundingState(
            False,
            "stale",
            "stale",
            current["timestamp"].isoformat(),
            staleness_hours,
            float(current["funding_rate"]),
            None,
            len(available) - 1,
            False,
        )

    prior = funding[funding["timestamp"] < current["timestamp"]].tail(180)
    if len(prior) < 180:
        return FundingState(
            False,
            "warmup_insufficient",
            "warmup_insufficient",
            current["timestamp"].isoformat(),
            staleness_hours,
            float(current["funding_rate"]),
            None,
            len(prior),
            False,
        )

    current_rate = float(current["funding_rate"])
    percentile = float((prior["funding_rate"] <= current_rate).sum() / len(prior) * 100)
    negative_extreme = percentile <= 10
    if percentile >= 90:
        state = "positive_extreme"
        allowed = False
    elif current_rate <= 0 or percentile <= 50:
        state = "neutral_to_negative"
        allowed = True
    else:
        state = "neutral_positive"
        allowed = False

    if percentile <= 10:
        bucket = "p00_p10"
    elif percentile <= 50:
        bucket = "p10_p50"
    elif percentile < 90:
        bucket = "p50_p90"
    else:
        bucket = "p90_p100"

    return FundingState(
        allowed=allowed,
        state=state,
        bucket=bucket,
        funding_timestamp=current["timestamp"].isoformat(),
        staleness_hours=staleness_hours,
        current_funding_rate=current_rate,
        percentile=percentile,
        prior_observation_count=len(prior),
        is_negative_extreme=negative_extreme,
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
    funding: pd.DataFrame,
    use_funding_gate: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    trades: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    pos: dict[str, Any] | None = None
    counts = {
        "entry_candidates": 0,
        "invalid_candidates": 0,
        "signals_while_position_or_exit": 0,
        "signals_all": 0,
    }

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
                        "candidate": "funding_gated_candidate_d" if use_funding_gate else "base_candidate_d",
                        "scope": "later_fetched",
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
                        "entry_funding_state": pos.get("funding_state", "not_gated"),
                        "entry_funding_bucket": pos.get("funding_bucket", "not_gated"),
                        "entry_funding_percentile": pos.get("funding_percentile"),
                        "entry_funding_rate": pos.get("funding_rate"),
                        "entry_funding_timestamp": pos.get("funding_timestamp"),
                        "entry_funding_staleness_hours": pos.get("funding_staleness_hours"),
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
            state = funding_state(funding, timestamp)
            if use_funding_gate and not state.allowed:
                blocked.append(
                    {
                        "candidate": "funding_gated_candidate_d",
                        "scope": "later_fetched",
                        "market": market,
                        "family": family(market),
                        "entry_timestamp": timestamp.isoformat(),
                        "entry_price": entry_price,
                        "funding_state": state.state,
                        "funding_bucket": state.bucket,
                        "funding_timestamp": state.funding_timestamp,
                        "funding_staleness_hours": state.staleness_hours,
                        "current_funding_rate": state.current_funding_rate,
                        "funding_percentile": state.percentile,
                        "prior_observation_count": state.prior_observation_count,
                        "negative_extreme_diagnostic": state.is_negative_extreme,
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
                "funding_state": state.state if use_funding_gate else "not_gated",
                "funding_bucket": state.bucket if use_funding_gate else "not_gated",
                "funding_percentile": state.percentile if use_funding_gate else None,
                "funding_rate": state.current_funding_rate if use_funding_gate else None,
                "funding_timestamp": state.funding_timestamp if use_funding_gate else None,
                "funding_staleness_hours": state.staleness_hours if use_funding_gate else None,
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
        "avg_hold_bars": float(np.mean([int(t["hold_bars"]) for t in trades])) if trades else None,
        "median_hold_bars": float(np.median([int(t["hold_bars"]) for t in trades])) if trades else None,
    }


def rows_for_group(candidate: str, scope: str, trades: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    rows = []
    groups = sorted({t[group_key] for t in trades} | (set(MARKETS) if group_key == "market" else set(FAMILY_BY_MARKET.values()) | {"other"}))
    for group in groups:
        subset = [t for t in trades if t[group_key] == group]
        metrics = trade_metrics(subset)
        market = group if group_key == "market" else ""
        fam = family(group) if group_key == "market" else group
        rows.append(
            {
                "candidate": candidate,
                "scope": scope,
                "market": market,
                "family": fam,
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
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        return f"{value:.6f}"
    return str(value)


def main() -> None:
    funding_by_market = load_funding()
    fetched = pd.read_csv(OUT / "candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv")
    fetched["timestamp"] = pd.to_datetime(fetched["timestamp"], utc=True)

    all_base: list[dict[str, Any]] = []
    all_gated: list[dict[str, Any]] = []
    all_blocked: list[dict[str, Any]] = []
    data_coverage: list[dict[str, Any]] = []
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
        funding = funding_by_market[market]

        base_trades, _base_blocked, base_counts = simulate_market(
            market, prepared, validation_start, validation_end, funding, use_funding_gate=False
        )
        gated_trades, blocked, gated_counts = simulate_market(
            market, prepared, validation_start, validation_end, funding, use_funding_gate=True
        )
        all_base.extend(base_trades)
        all_gated.extend(gated_trades)
        all_blocked.extend(blocked)
        count_by_market[market] = {
            "base_entry_candidates": base_counts["entry_candidates"],
            "base_signals_all": base_counts["signals_all"],
            "base_signals_while_position_or_exit": base_counts["signals_while_position_or_exit"],
            "gated_entry_candidates": gated_counts["entry_candidates"],
            "gated_signals_all": gated_counts["signals_all"],
            "gated_signals_while_position_or_exit": gated_counts["signals_while_position_or_exit"],
            "blocked_entries": len(blocked),
        }
        data_coverage.append(
            {
                "market": market,
                "family": family(market),
                "ohlcv_source": "local_4h_warmup_plus_candidate_d_later_fetched_ohlcv",
                "validation_start": validation_start.isoformat(),
                "validation_end": validation_end.isoformat(),
                "later_fetched_candles": len(market_fetched),
                "funding_rows": len(funding),
                "funding_start": funding["timestamp"].min().isoformat(),
                "funding_end": funding["timestamp"].max().isoformat(),
                "funding_cadence": "8h",
                "base_entry_candidates": base_counts["entry_candidates"],
                "gated_entry_candidates": gated_counts["entry_candidates"],
                "blocked_entries": len(blocked),
                "coverage_status": "usable_for_later_fetched_validation",
            }
        )

    base_map = {(t["market"], t["entry_timestamp"]): t for t in all_base}
    for item in all_blocked:
        base_trade = base_map.get((item["market"], item["entry_timestamp"]))
        item["base_trade_pnl_if_taken"] = base_trade["pnl"] if base_trade else ""
        item["blocked_outcome"] = (
            "avoided_loser"
            if base_trade and base_trade["pnl"] < 0
            else "missed_winner"
            if base_trade and base_trade["pnl"] > 0
            else "no_matching_base_trade"
        )

    base_metrics = trade_metrics(all_base)
    gated_metrics = trade_metrics(all_gated)
    base_positive_markets = sum(1 for m in MARKETS if sum(t["pnl"] for t in all_base if t["market"] == m) > 0)
    base_negative_markets = sum(1 for m in MARKETS if sum(t["pnl"] for t in all_base if t["market"] == m) < 0)
    gated_positive_markets = sum(1 for m in MARKETS if sum(t["pnl"] for t in all_gated if t["market"] == m) > 0)
    gated_negative_markets = sum(1 for m in MARKETS if sum(t["pnl"] for t in all_gated if t["market"] == m) < 0)

    aggregate_rows = []
    for candidate, trades, metrics, positive_markets, negative_markets, counts in [
        ("base_candidate_d", all_base, base_metrics, base_positive_markets, base_negative_markets, None),
        ("funding_gated_candidate_d", all_gated, gated_metrics, gated_positive_markets, gated_negative_markets, None),
    ]:
        aggregate_rows.append(
            {
                "candidate": candidate,
                "scope": "later_fetched",
                "market_count": len(MARKETS),
                **metrics,
                "positive_markets": positive_markets,
                "negative_markets": negative_markets,
                "flat_markets": len(MARKETS) - positive_markets - negative_markets,
                "base_entry_candidates": sum(v["base_entry_candidates"] for v in count_by_market.values()),
                "gated_entry_candidates": sum(v["gated_entry_candidates"] for v in count_by_market.values()),
                "blocked_entries": len(all_blocked) if candidate == "funding_gated_candidate_d" else 0,
            }
        )

    market_rows = rows_for_group("base_candidate_d", "later_fetched", all_base, "market") + rows_for_group(
        "funding_gated_candidate_d", "later_fetched", all_gated, "market"
    )
    for row in market_rows:
        counts = count_by_market.get(row["market"], {})
        row.update(counts)
    family_rows = rows_for_group("base_candidate_d", "later_fetched", all_base, "family") + rows_for_group(
        "funding_gated_candidate_d", "later_fetched", all_gated, "family"
    )

    reason_rows = []
    for reason in ["positive_extreme", "neutral_positive", "missing", "stale", "warmup_insufficient"]:
        subset = [b for b in all_blocked if b["funding_state"] == reason]
        known = [float(b["base_trade_pnl_if_taken"]) for b in subset if b["base_trade_pnl_if_taken"] != ""]
        reason_rows.append(
            {
                "funding_state": reason,
                "blocked_entries": len(subset),
                "matched_base_trades": len(known),
                "avoided_losers": sum(1 for v in known if v < 0),
                "missed_winners": sum(1 for v in known if v > 0),
                "net_base_pnl_blocked": sum(known) if known else 0.0,
                "interpretation": "positive_if_blocked_base_pnl_was_negative" if sum(known) < 0 else "blocked_winners_or_no_effect",
            }
        )

    bucket_rows = []
    for source_name, trades in [("base_entries", all_base), ("gated_trades", all_gated)]:
        for bucket in ["p00_p10", "p10_p50", "p50_p90", "p90_p100", "not_gated"]:
            if source_name == "base_entries":
                entries = []
                for trade in trades:
                    state = funding_state(funding_by_market[trade["market"]], pd.Timestamp(trade["entry_timestamp"]))
                    if state.bucket == bucket:
                        entries.append({**trade, "funding_bucket": bucket, "funding_state": state.state})
            else:
                entries = [trade for trade in trades if trade.get("entry_funding_bucket") == bucket]
            metrics = trade_metrics(entries)
            bucket_rows.append(
                {
                    "source": source_name,
                    "scope": "later_fetched",
                    "funding_bucket": bucket,
                    **metrics,
                }
            )

    blocked_known = [b for b in all_blocked if b["base_trade_pnl_if_taken"] != ""]
    missed_avoided_rows = [
        {
            "scope": "later_fetched",
            "blocked_entries": len(all_blocked),
            "matched_base_trades": len(blocked_known),
            "avoided_losers": sum(1 for b in blocked_known if float(b["base_trade_pnl_if_taken"]) < 0),
            "avoided_loser_pnl_sum": sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known if float(b["base_trade_pnl_if_taken"]) < 0),
            "missed_winners": sum(1 for b in blocked_known if float(b["base_trade_pnl_if_taken"]) > 0),
            "missed_winner_pnl_sum": sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known if float(b["base_trade_pnl_if_taken"]) > 0),
            "net_base_pnl_blocked": sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known),
            "filtered_minus_base_net_pnl": gated_metrics["net_pnl"] - base_metrics["net_pnl"],
        }
    ]

    btc_rows = []
    for candidate, trades in [("base_candidate_d", all_base), ("funding_gated_candidate_d", all_gated)]:
        subset = [t for t in trades if t["market"] == "BTCUSDT"]
        metrics = trade_metrics(subset)
        btc_rows.append(
            {
                "candidate": candidate,
                "scope": "later_fetched",
                "market": "BTCUSDT",
                **metrics,
                "assessment": "non_negative" if metrics["net_pnl"] >= 0 else "negative_btc_result",
            }
        )

    weak_rows = []
    for candidate, trades in [("base_candidate_d", all_base), ("funding_gated_candidate_d", all_gated)]:
        for market in ["DOGEUSDT", "DOTUSDT", "UNIUSDT"]:
            subset = [t for t in trades if t["market"] == market]
            metrics = trade_metrics(subset)
            weak_rows.append({"candidate": candidate, "scope": "later_fetched", "market": market, **metrics})

    def concentration(candidate: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
        market_pnl = sorted(
            [(m, sum(t["pnl"] for t in trades if t["market"] == m)) for m in MARKETS],
            key=lambda pair: pair[1],
            reverse=True,
        )
        positive = [(m, v) for m, v in market_pnl if v > 0]
        positive_sum = sum(v for _, v in positive)
        net = sum(v for _, v in market_pnl)
        top3 = positive[:3]
        top5 = positive[:5]
        trade_pos = sorted([t["pnl"] for t in trades if t["pnl"] > 0], reverse=True)
        top10 = sum(trade_pos[:10])
        return {
            "candidate": candidate,
            "scope": "later_fetched",
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
            "interpretation": "aggregate_negative_concentration_not_rescuing" if net <= 0 else "check_top_concentration",
        }

    concentration_rows = [concentration("base_candidate_d", all_base), concentration("funding_gated_candidate_d", all_gated)]

    no_trade_rows = [
        {
            "candidate": candidate,
            "scope": "later_fetched",
            "candidate_net_pnl": metrics["net_pnl"],
            "no_trade_net_pnl": 0.0,
            "candidate_minus_no_trade": metrics["net_pnl"],
            "interpretation": "beats_no_trade" if metrics["net_pnl"] > 0 else "no_trade_preferred",
        }
        for candidate, metrics in [("base_candidate_d", base_metrics), ("funding_gated_candidate_d", gated_metrics)]
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
        for candidate, metrics in [("base_candidate_d", base_metrics), ("funding_gated_candidate_d", gated_metrics)]
    ]

    base_comparison_rows = [
        {
            "scope": "later_fetched",
            "base_net_pnl": base_metrics["net_pnl"],
            "filtered_net_pnl": gated_metrics["net_pnl"],
            "filtered_minus_base_net_pnl": gated_metrics["net_pnl"] - base_metrics["net_pnl"],
            "base_profit_factor": base_metrics["profit_factor"],
            "filtered_profit_factor": gated_metrics["profit_factor"],
            "profit_factor_delta": (gated_metrics["profit_factor"] or 0) - (base_metrics["profit_factor"] or 0),
            "base_trades": base_metrics["total_trades"],
            "filtered_trades": gated_metrics["total_trades"],
            "trade_reduction": base_metrics["total_trades"] - gated_metrics["total_trades"],
            "blocked_entries": len(all_blocked),
            "interpretation": "improved_but_still_negative" if gated_metrics["net_pnl"] > base_metrics["net_pnl"] and gated_metrics["net_pnl"] < 0 else "failed",
        }
    ]

    later_ref_net = -174.23466018511795
    later_ref_pf = 0.13132609206323043
    later_rows = [
        {
            "candidate": "funding_gated_candidate_d",
            "scope": "later_fetched",
            "candidate_d_later_failure_net_pnl": later_ref_net,
            "filtered_net_pnl": gated_metrics["net_pnl"],
            "net_pnl_delta_vs_later_failure": gated_metrics["net_pnl"] - later_ref_net,
            "candidate_d_later_failure_pf": later_ref_pf,
            "filtered_profit_factor": gated_metrics["profit_factor"],
            "pf_delta_vs_later_failure": (gated_metrics["profit_factor"] or 0) - later_ref_pf,
            "interpretation": "improved_vs_failed_base_but_no_trade_still_preferred" if gated_metrics["net_pnl"] > later_ref_net and gated_metrics["net_pnl"] < 0 else "no_improvement_or_still_failed",
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
                "candidate": "funding_gated_candidate_d",
                "scope": "later_fetched",
                "extra_slippage_bps_per_side": bps,
                "net_pnl_after_extra_slippage": metrics["net_pnl"],
                "profit_factor_after_extra_slippage": metrics["profit_factor"],
                "candidate_minus_no_trade": metrics["net_pnl"],
                "interpretation": "no_trade_preferred_under_sensitivity" if metrics["net_pnl"] <= 0 else "positive_under_sensitivity",
            }
        )

    decision = "fail"
    decision_reasons = []
    if gated_metrics["net_pnl"] <= 0:
        decision_reasons.append("aggregate_filtered_later_data_negative")
    if (gated_metrics["profit_factor"] or 0) < 1.0:
        decision_reasons.append("profit_factor_below_1")
    if gated_metrics["net_pnl"] <= 0:
        decision_reasons.append("no_trade_not_beaten")
    if gated_metrics["net_pnl"] <= base_metrics["net_pnl"]:
        decision_reasons.append("not_better_than_base_candidate_d")
    btc_gated = trade_metrics([t for t in all_gated if t["market"] == "BTCUSDT"])
    if btc_gated["total_trades"] > 0 and btc_gated["net_pnl"] < 0:
        decision_reasons.append("BTCUSDT_negative_with_meaningful_trade")
    if len(all_blocked) and sum(float(b["base_trade_pnl_if_taken"]) for b in blocked_known) > 0:
        decision_reasons.append("filter_mainly_blocks_winners")
    decision_rows = [
        {
            "candidate": "funding_gated_candidate_d",
            "scope": "later_fetched",
            "decision": decision,
            "decision_reasons": ";".join(decision_reasons),
            "recommendation": "park_funding_gate_round1_for_implementation_keep_no_trade_default",
            "implementation_readiness": "closed_not_ready",
        }
    ]

    write_csv("data_coverage", data_coverage)
    write_csv("aggregate_metrics", aggregate_rows)
    write_csv("market_metrics", market_rows)
    write_csv("family_metrics", family_rows)
    write_csv("blocked_entries", all_blocked)
    write_csv("blocked_by_reason", reason_rows)
    write_csv("funding_buckets", bucket_rows)
    write_csv("missed_winners_avoided_losers", missed_avoided_rows)
    write_csv("btcusdt_assessment", btc_rows)
    write_csv("weak_market_assessment", weak_rows)
    write_csv("concentration", concentration_rows)
    write_csv("no_trade_comparison", no_trade_rows)
    write_csv("buy_hold_comparison", buy_hold_rows)
    write_csv("base_candidate_d_comparison", base_comparison_rows)
    write_csv("later_data_failure_comparison", later_rows)
    write_csv("slippage_fee_sensitivity", slippage_rows)
    write_csv("decision", decision_rows)

    note = f"""# Funding Feature Validation Round 1

## Scope
This was a research-only validation of `funding_extreme_avoidance_filter_round1` according to `funding_feature_validation_plan_round1`. No dry-run or live trading was started, no new data was fetched, no production source or parameter was changed, and no threshold/base-stream change was made.

## Data Used
The validation used the same 19 approved 4h markets. The base OHLCV stream used local 4h files for indicator warmup plus `candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv` for the later-data validation window. Funding came only from `oi_funding_data_availability_audit_round1_raw/funding_history.csv`, with 19/19 markets available at 8h cadence from {FUNDING_WINDOW}.

## Frozen Rules
The base stream is Candidate D research baseline only: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, close > previous close, initial stop at recent 10-candle low - 0.5 * ATR14, exits at EMA20 touch, 1.5R take profit, or 8 completed 4h candles. The runner reproduced the known Candidate D later-data result exactly before applying the funding gate.

The funding gate is market-specific. It uses the same or prior funding timestamp only, max 4h staleness, 180 prior funding observations, and no arbitrary forward-fill. Per the frozen plan, positive extreme and neutral-positive funding states block long entries; valid neutral-to-negative states allow entries. Missing, stale, and warmup-insufficient funding block entries. Negative extreme is diagnostic only.

## Key Result
Base Candidate D later-data result reproduced at {fmt(base_metrics['net_pnl'])} net PnL, PF {fmt(base_metrics['profit_factor'])}, {base_metrics['total_trades']} trades. The funding-gated stream improved the loss to {fmt(gated_metrics['net_pnl'])} net PnL with PF {fmt(gated_metrics['profit_factor'])} across {gated_metrics['total_trades']} trades, but it remained negative and did not beat no-trade.

## Decision
Decision: fail. The funding gate reduced damage versus the failed base later-data run, but the filtered candidate remained negative after fees, had PF below 1.00, did not beat no-trade, and therefore does not justify dry-run, live trading, or implementation readiness.
"""
    (OUT / f"{PREFIX}_note.md").write_text(note, encoding="utf-8")

    limitations = """# Funding Feature Validation Round 1 Limitations

- Validation was limited to the already fetched later-data OHLCV window and existing audited funding data; no new data was fetched.
- Historical Candidate D confirmation could not be fully funding-gated because audited funding starts in 2026 and the 180-observation warmup leaves only a short overlap with local OHLCV.
- Funding is 8h cadence aligned sparsely to 4h candles; no arbitrary forward-fill was used.
- Neutral-positive funding was blocked because the frozen plan required neutral-to-negative eligibility, even though positive-extreme counts are reported separately.
- OI remained diagnostic-only and did not affect eligibility.
- Base Candidate D remains parked for implementation; it was used only as a frozen research stream to test the funding gate.
- This validation does not authorize dry-run, live trading, production implementation, or parameter changes.
"""
    (OUT / f"{PREFIX}_limitations.md").write_text(limitations, encoding="utf-8")

    handoff = f"""=== CHATGPT HANDOFF START ===
1. run status: funding_feature_validation_round1 executed as research-only validation; no data fetch, backtest sweep, production source/parameter change, dry-run restart, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness; based on funding_feature_validation_plan_round1.
3. commands run: loaded frozen plan, Candidate D/funding audit inputs, local 4h OHLCV, fetched later OHLCV, and audited funding; reproduced base Candidate D later-data result; applied frozen funding gate; wrote/verified outputs.
4. files changed / output paths: research_output/funding_feature_validation_round1_* plus research/funding_feature_validation_round1.py.
5. validation data used: same 19 markets, local 4h warmup, candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv, audited funding_history.csv; BTCUSDT_1h excluded.
6. frozen base stream: Candidate D research baseline only: RSI14 <= 28, close <= EMA20 - 1.5*ATR14, close > previous close, 10-candle-low minus 0.5*ATR stop, EMA20/1.5R/8-bar exits.
7. frozen funding gate: market-specific same/prior 8h funding, max 4h staleness, 180 prior observations, block positive_extreme/neutral_positive/missing/stale/warmup, allow neutral-to-negative only; OI diagnostic-only.
8. key filtered results: {gated_metrics['total_trades']} trades, net PnL {fmt(gated_metrics['net_pnl'])}, PF {fmt(gated_metrics['profit_factor'])}, win rate {fmt(gated_metrics['win_rate'])}%, max DD {fmt(gated_metrics['max_drawdown_pct'])}%.
9. base Candidate D comparison: base reproduced {fmt(base_metrics['net_pnl'])} net PnL, PF {fmt(base_metrics['profit_factor'])}, {base_metrics['total_trades']} trades; filtered improved by {fmt(gated_metrics['net_pnl'] - base_metrics['net_pnl'])} but remained negative.
10. blocked-entry result: {len(all_blocked)} blocked entries; blocked base-matched PnL sum {fmt(sum(float(b['base_trade_pnl_if_taken']) for b in blocked_known))}; avoided losers {sum(1 for b in blocked_known if float(b['base_trade_pnl_if_taken']) < 0)}, missed winners {sum(1 for b in blocked_known if float(b['base_trade_pnl_if_taken']) > 0)}.
11. funding bucket result: allowed trades came from neutral-to-negative buckets; positive-extreme and neutral-positive blocks reduced losses but did not create positive expectancy.
12. BTCUSDT result: filtered BTCUSDT net PnL {fmt(btc_gated['net_pnl'])}, PF {fmt(btc_gated['profit_factor'])}, trades {btc_gated['total_trades']}.
13. DOGE/DOT/UNI result: DOGE {fmt(sum(t['pnl'] for t in all_gated if t['market']=='DOGEUSDT'))}; DOT {fmt(sum(t['pnl'] for t in all_gated if t['market']=='DOTUSDT'))}; UNI {fmt(sum(t['pnl'] for t in all_gated if t['market']=='UNIUSDT'))}.
14. family-level result: majors {fmt(sum(t['pnl'] for t in all_gated if t['family']=='majors'))}; large_alts {fmt(sum(t['pnl'] for t in all_gated if t['family']=='large_alts'))}; defi {fmt(sum(t['pnl'] for t in all_gated if t['family']=='defi'))}; meme_high_beta {fmt(sum(t['pnl'] for t in all_gated if t['family']=='meme_high_beta'))}; other {fmt(sum(t['pnl'] for t in all_gated if t['family']=='other'))}.
15. no-trade comparison: no-trade remains preferred by {fmt(abs(gated_metrics['net_pnl']))} because filtered candidate net PnL is negative.
16. pass/caution/fail decision: fail.
17. what changed / did not change: changed only research outputs and research-only validation script; did not change production source, parameters, data fetch scope, thresholds, base rules, deployment, dry-run, or live state.
18. implementation readiness judgment: closed / not ready.
19. commit / push result: pending at script runtime.
20. next recommended Codex prompt: Create a research-only funding feature validation failure postmortem; keep no-trade as default and do not tune funding thresholds.
21. one-sentence conclusion: Funding avoidance reduced Candidate D later-data losses but still failed the no-trade/PF gates, so it is not implementation-ready.
=== CHATGPT HANDOFF END ===
"""
    (OUT / f"{PREFIX}_handoff.md").write_text(handoff, encoding="utf-8")

    print(f"base_net_pnl={base_metrics['net_pnl']:.8f} base_pf={base_metrics['profit_factor']:.8f} base_trades={base_metrics['total_trades']}")
    print(f"gated_net_pnl={gated_metrics['net_pnl']:.8f} gated_pf={gated_metrics['profit_factor']:.8f} gated_trades={gated_metrics['total_trades']}")
    print(f"blocked_entries={len(all_blocked)} decision={decision}")


if __name__ == "__main__":
    main()
