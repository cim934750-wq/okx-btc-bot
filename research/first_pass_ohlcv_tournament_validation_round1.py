
from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_output"
PREFIX = "first_pass_ohlcv_tournament_validation_round1"

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

KEY_MARKETS = ["BTCUSDT", "DOGEUSDT", "DOTUSDT", "UNIUSDT"]
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

CANDIDATES = [
    "A_ts_momentum_ema_return_round1",
    "B_cross_sectional_top3_round1",
    "C_donchian_breakout_round1",
    "D_vol_contraction_breakout_round1",
    "E_rsi_bollinger_reversion_round1",
    "I_regime_filtered_trend_round1",
]

CANDIDATE_NAMES = {
    "A_ts_momentum_ema_return_round1": "Time-series EMA/return momentum",
    "B_cross_sectional_top3_round1": "Cross-sectional top-3 relative strength",
    "C_donchian_breakout_round1": "Donchian channel breakout",
    "D_vol_contraction_breakout_round1": "Bollinger bandwidth contraction breakout",
    "E_rsi_bollinger_reversion_round1": "RSI/Bollinger oversold reversion",
    "I_regime_filtered_trend_round1": "BTC regime-filtered generic trend",
}

FAMILY_BY_CANDIDATE = {
    "A_ts_momentum_ema_return_round1": "A",
    "B_cross_sectional_top3_round1": "B",
    "C_donchian_breakout_round1": "C",
    "D_vol_contraction_breakout_round1": "D",
    "E_rsi_bollinger_reversion_round1": "E",
    "I_regime_filtered_trend_round1": "I",
}

STARTING_EQUITY = 100_000.0
FIXED_NOTIONAL = 1_000.0
FEE_RATE = 0.0005
EXTRA_SLIPPAGE_BPS = [0.0, 2.5, 5.0, 10.0]
SPLIT_FRACTION = 0.70


@dataclass
class Trade:
    candidate: str
    scope: str
    market: str
    family: str
    entry_timestamp: pd.Timestamp
    exit_timestamp: pd.Timestamp
    entry_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    stop_price: float
    exit_reason: str
    hold_bars: int
    size: float
    gross_pnl: float
    commission: float
    pnl: float

    def as_row(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate,
            "scope": self.scope,
            "market": self.market,
            "family": self.family,
            "entry_timestamp": self.entry_timestamp.isoformat(),
            "exit_timestamp": self.exit_timestamp.isoformat(),
            "entry_index": self.entry_index,
            "exit_index": self.exit_index,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "stop_price": self.stop_price,
            "exit_reason": self.exit_reason,
            "hold_bars": self.hold_bars,
            "size": self.size,
            "gross_pnl": self.gross_pnl,
            "commission": self.commission,
            "pnl": self.pnl,
        }


def family(market: str) -> str:
    return FAMILY_BY_MARKET.get(market, "other")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        if not fields:
            fields = ["note"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0).rolling(length).mean()
    loss = (-delta.clip(upper=0.0)).rolling(length).mean()
    rs = gain / loss.replace(0.0, np.nan)
    return 100 - (100 / (1 + rs))


def percentile_vs_prior(series: pd.Series, lookback: int) -> pd.Series:
    values = series.to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    for idx in range(lookback, len(values)):
        current = values[idx]
        prior = values[idx - lookback: idx]
        prior = prior[np.isfinite(prior)]
        if np.isfinite(current) and len(prior) == lookback:
            out[idx] = float((prior <= current).sum() / len(prior) * 100.0)
    return pd.Series(out, index=series.index)


def load_market(market: str) -> pd.DataFrame:
    path = ROOT / "data" / f"{market}_4h.csv"
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last").reset_index(drop=True)
    df["market"] = market
    df["row_index"] = np.arange(len(df))
    split_idx = int(math.floor(len(df) * SPLIT_FRACTION))
    df["scope"] = np.where(df["row_index"] < split_idx, "reference", "holdout")

    df["ema50"] = ema(df["close"], 50)
    df["ema100"] = ema(df["close"], 100)
    df["ema200"] = ema(df["close"], 200)
    df["sma20"] = df["close"].rolling(20).mean()
    df["atr14"] = true_range(df["high"], df["low"], df["close"]).rolling(14).mean()
    df["rsi14"] = rsi(df["close"], 14)
    df["return20"] = df["close"] / df["close"].shift(20) - 1.0
    df["return180"] = df["close"] / df["close"].shift(180) - 1.0
    df["bb_std20"] = df["close"].rolling(20).std()
    df["bb_upper20_2"] = df["sma20"] + 2.0 * df["bb_std20"]
    df["bb_lower20_2"] = df["sma20"] - 2.0 * df["bb_std20"]
    df["bb_width20_2"] = (df["bb_upper20_2"] - df["bb_lower20_2"]) / df["sma20"].replace(0.0, np.nan)
    df["bb_width_pct120"] = percentile_vs_prior(df["bb_width20_2"], 120)
    df["volume_median20"] = df["volume"].rolling(20).median()
    df["prior55_high"] = df["high"].shift(1).rolling(55).max()
    df["prior20_low"] = df["low"].shift(1).rolling(20).min()
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df["realized_vol60"] = df["log_return"].rolling(60).std()
    df["realized_vol60_pct180"] = percentile_vs_prior(df["realized_vol60"], 180)
    return df


def commission(entry_price: float, exit_price: float, size: float, fee_rate: float = FEE_RATE) -> float:
    return (entry_price + exit_price) * size * fee_rate


def make_trade(candidate: str, scope: str, market: str, entry: dict[str, Any], row: pd.Series, exit_price: float, reason: str) -> Trade:
    size = float(entry["size"])
    gross = (exit_price - float(entry["entry_price"])) * size
    fee = commission(float(entry["entry_price"]), exit_price, size)
    return Trade(
        candidate=candidate,
        scope=scope,
        market=market,
        family=family(market),
        entry_timestamp=entry["entry_timestamp"],
        exit_timestamp=pd.Timestamp(row["timestamp"]),
        entry_index=int(entry["entry_index"]),
        exit_index=int(row["row_index"]),
        entry_price=float(entry["entry_price"]),
        exit_price=float(exit_price),
        stop_price=float(entry["stop_price"]),
        exit_reason=reason,
        hold_bars=int(row["row_index"] - entry["entry_index"]),
        size=size,
        gross_pnl=gross,
        commission=fee,
        pnl=gross - fee,
    )


def finite(*values: Any) -> bool:
    return all(v is not None and math.isfinite(float(v)) for v in values)


def entry_signal(candidate: str, row: pd.Series, btc_regime_on: bool | None = None) -> bool:
    close = float(row["close"])
    if candidate == "A_ts_momentum_ema_return_round1":
        return finite(row["ema100"], row["return20"]) and close > float(row["ema100"]) and float(row["return20"]) > 0
    if candidate == "C_donchian_breakout_round1":
        return finite(row["prior55_high"]) and close > float(row["prior55_high"])
    if candidate == "D_vol_contraction_breakout_round1":
        return (
            finite(row["bb_width_pct120"], row["bb_upper20_2"], row["volume_median20"], row["atr14"])
            and float(row["bb_width_pct120"]) <= 20.0
            and close > float(row["bb_upper20_2"])
            and float(row["volume"]) > float(row["volume_median20"])
        )
    if candidate == "E_rsi_bollinger_reversion_round1":
        return finite(row["bb_lower20_2"], row["rsi14"]) and close < float(row["bb_lower20_2"]) and float(row["rsi14"]) < 30.0
    if candidate == "I_regime_filtered_trend_round1":
        return bool(btc_regime_on) and finite(row["ema100"]) and close > float(row["ema100"])
    raise ValueError(f"unsupported candidate {candidate}")


def initial_stop(candidate: str, row: pd.Series) -> float | None:
    close = float(row["close"])
    if candidate in {"A_ts_momentum_ema_return_round1", "I_regime_filtered_trend_round1"}:
        if not finite(row["atr14"]):
            return None
        return close - 2.0 * float(row["atr14"])
    if candidate == "C_donchian_breakout_round1":
        if not finite(row["prior20_low"], row["atr14"]):
            return None
        return max(float(row["prior20_low"]), close - 2.0 * float(row["atr14"]))
    if candidate == "D_vol_contraction_breakout_round1":
        if not finite(row["atr14"]):
            return None
        return close - 1.5 * float(row["atr14"])
    if candidate == "E_rsi_bollinger_reversion_round1":
        if not finite(row["atr14"]):
            return None
        return float(row["low"]) - 1.0 * float(row["atr14"])
    raise ValueError(f"unsupported candidate {candidate}")


def exit_for_position(candidate: str, row: pd.Series, pos: dict[str, Any], btc_regime_on: bool | None = None) -> tuple[str, float] | None:
    if float(row["low"]) <= float(pos["stop_price"]):
        return "stop_loss", float(pos["stop_price"])
    hold = int(row["row_index"] - pos["entry_index"])
    close = float(row["close"])
    if candidate == "A_ts_momentum_ema_return_round1":
        if finite(row["ema50"]) and close < float(row["ema50"]):
            return "ema50_loss", close
        if hold >= 12:
            return "time_stop_12_bars", close
    elif candidate == "C_donchian_breakout_round1":
        if finite(row["prior20_low"]) and close < float(row["prior20_low"]):
            return "donchian20_low_exit", close
    elif candidate == "D_vol_contraction_breakout_round1":
        if finite(row["sma20"]) and close < float(row["sma20"]):
            return "sma20_loss", close
        if hold >= 8:
            return "time_stop_8_bars", close
    elif candidate == "E_rsi_bollinger_reversion_round1":
        if finite(row["sma20"]) and float(row["high"]) >= float(row["sma20"]):
            return "sma20_touch", float(row["sma20"])
        if finite(row["rsi14"]) and float(row["rsi14"]) > 50.0:
            return "rsi14_above_50", close
        if hold >= 8:
            return "time_stop_8_bars", close
    elif candidate == "I_regime_filtered_trend_round1":
        if not bool(btc_regime_on):
            return "btc_regime_off", close
        if finite(row["ema50"]) and close < float(row["ema50"]):
            return "ema50_loss", close
    return None


def compute_btc_regime(btc: pd.DataFrame) -> pd.DataFrame:
    cols = ["timestamp", "close", "ema200", "realized_vol60", "realized_vol60_pct180"]
    reg = btc[cols].copy()
    reg["btc_regime_on"] = (
        reg["close"].gt(reg["ema200"])
        & reg["realized_vol60_pct180"].lt(75.0)
        & reg["ema200"].notna()
        & reg["realized_vol60_pct180"].notna()
    )
    return reg[["timestamp", "btc_regime_on"]]


def attach_btc_regime(df: pd.DataFrame, btc_regime: pd.DataFrame) -> pd.DataFrame:
    return pd.merge_asof(
        df.sort_values("timestamp"),
        btc_regime.sort_values("timestamp"),
        on="timestamp",
        direction="backward",
    )


def scope_bounds(df: pd.DataFrame, scope: str) -> tuple[int, int] | None:
    idx = df.index[df["scope"] == scope].to_list()
    if not idx:
        return None
    return idx[0], idx[-1]


def simulate_market_candidate(candidate: str, market: str, data: pd.DataFrame, scope: str) -> tuple[list[Trade], dict[str, Any]]:
    trades: list[Trade] = []
    counts: dict[str, Any] = {
        "candidate": candidate,
        "scope": scope,
        "market": market,
        "raw_signals": 0,
        "entry_candidates": 0,
        "invalid_stop_skips": 0,
        "signals_while_position_or_exit": 0,
        "warmup_loss_count": 0,
        "open_position_at_scope_end": 0,
        "skipped_entries": 0,
        "skip_reasons": "",
    }
    bounds = scope_bounds(data, scope)
    if bounds is None:
        counts["skip_reasons"] = "no_scope_rows"
        return trades, counts
    start, end = bounds
    pos: dict[str, Any] | None = None
    skipped_reasons: list[str] = []
    for idx in range(start, end + 1):
        row = data.iloc[idx]
        exited_this_bar = False
        btc_regime_on = bool(row.get("btc_regime_on", False)) if candidate == "I_regime_filtered_trend_round1" else None
        if pos is not None:
            exit_data = exit_for_position(candidate, row, pos, btc_regime_on)
            if exit_data is not None:
                reason, price = exit_data
                trades.append(make_trade(candidate, scope, market, pos, row, price, reason))
                pos = None
                exited_this_bar = True
        signal = entry_signal(candidate, row, btc_regime_on)
        if signal:
            counts["raw_signals"] += 1
            if pos is not None or exited_this_bar:
                counts["signals_while_position_or_exit"] += 1
                skipped_reasons.append("position_open_or_exited_same_bar")
                continue
            stop = initial_stop(candidate, row)
            if stop is None or not math.isfinite(stop) or stop >= float(row["close"]):
                counts["invalid_stop_skips"] += 1
                skipped_reasons.append("invalid_or_nonfinite_stop")
                continue
            counts["entry_candidates"] += 1
            pos = {
                "entry_index": int(row["row_index"]),
                "entry_timestamp": pd.Timestamp(row["timestamp"]),
                "entry_price": float(row["close"]),
                "stop_price": float(stop),
                "size": FIXED_NOTIONAL / float(row["close"]),
            }
    if pos is not None:
        counts["open_position_at_scope_end"] = 1
        counts["skipped_entries"] += 1
        skipped_reasons.append("open_position_not_force_closed_at_scope_end")
    counts["skipped_entries"] += counts["invalid_stop_skips"] + counts["signals_while_position_or_exit"]
    counts["skip_reasons"] = "|".join(sorted(set(skipped_reasons)))
    # Warmup rows are rows in scope before every rule input for this candidate can first be finite.
    if candidate == "A_ts_momentum_ema_return_round1":
        ready = data["ema100"].notna() & data["return20"].notna() & data["atr14"].notna()
    elif candidate == "C_donchian_breakout_round1":
        ready = data["prior55_high"].notna() & data["prior20_low"].notna() & data["atr14"].notna()
    elif candidate == "D_vol_contraction_breakout_round1":
        ready = data["bb_width_pct120"].notna() & data["bb_upper20_2"].notna() & data["volume_median20"].notna() & data["atr14"].notna()
    elif candidate == "E_rsi_bollinger_reversion_round1":
        ready = data["bb_lower20_2"].notna() & data["rsi14"].notna() & data["atr14"].notna() & data["sma20"].notna()
    elif candidate == "I_regime_filtered_trend_round1":
        ready = data["ema100"].notna() & data["atr14"].notna() & data["btc_regime_on"].notna()
    else:
        ready = pd.Series(False, index=data.index)
    counts["warmup_loss_count"] = int((~ready.iloc[start:end + 1]).sum())
    return trades, counts


def simulate_b_candidate(market_data: dict[str, pd.DataFrame], scope: str) -> tuple[list[Trade], list[dict[str, Any]]]:
    candidate = "B_cross_sectional_top3_round1"
    trades: list[Trade] = []
    count_by_market: dict[str, dict[str, Any]] = {
        market: {
            "candidate": candidate,
            "scope": scope,
            "market": market,
            "raw_signals": 0,
            "entry_candidates": 0,
            "invalid_stop_skips": 0,
            "signals_while_position_or_exit": 0,
            "warmup_loss_count": 0,
            "open_position_at_scope_end": 0,
            "skipped_entries": 0,
            "skip_reasons": "",
        }
        for market in MARKETS
    }
    row_by_market: dict[str, pd.DataFrame] = {m: df[df["scope"] == scope].copy() for m, df in market_data.items()}
    all_times = sorted(set(pd.concat([df[["timestamp"]] for df in row_by_market.values() if not df.empty], ignore_index=True)["timestamp"]))
    if not all_times:
        return trades, list(count_by_market.values())
    row_lookup = {m: {pd.Timestamp(r["timestamp"]): r for _, r in df.iterrows()} for m, df in row_by_market.items()}
    start_time = min(all_times)
    next_rebalance = start_time
    positions: dict[str, dict[str, Any]] = {}
    skip_reasons: dict[str, set[str]] = {m: set() for m in MARKETS}

    for timestamp in all_times:
        # Stop check and trailing update on each market's closed 4h candle.
        for market in list(positions):
            row = row_lookup.get(market, {}).get(timestamp)
            if row is None:
                continue
            pos = positions[market]
            if float(row["low"]) <= float(pos["stop_price"]):
                trades.append(make_trade(candidate, scope, market, pos, row, float(pos["stop_price"]), "atr_trailing_stop"))
                del positions[market]
                continue
            if finite(row["atr14"]):
                positions[market]["stop_price"] = max(float(pos["stop_price"]), float(row["close"]) - 2.0 * float(row["atr14"]))

        if timestamp < next_rebalance:
            continue
        while next_rebalance <= timestamp:
            next_rebalance = next_rebalance + pd.Timedelta(days=7)

        ranking_rows: list[tuple[str, float, pd.Series]] = []
        for market in MARKETS:
            row = row_lookup.get(market, {}).get(timestamp)
            if row is None:
                skip_reasons[market].add("no_row_at_rebalance")
                continue
            if not finite(row["return180"], row["atr14"]):
                count_by_market[market]["warmup_loss_count"] += 1
                skip_reasons[market].add("rank_or_atr_warmup")
                continue
            ranking_rows.append((market, float(row["return180"]), row))
        ranking_rows.sort(key=lambda item: item[1], reverse=True)
        ranks = {market: rank + 1 for rank, (market, _value, _row) in enumerate(ranking_rows)}

        # Rank exit for positions that have fallen out of top half or no longer have positive momentum.
        for market in list(positions):
            row = row_lookup.get(market, {}).get(timestamp)
            rank = ranks.get(market)
            ret = next((value for name, value, _row in ranking_rows if name == market), None)
            if row is None or rank is None or rank > 9 or ret is None or ret <= 0:
                if row is not None:
                    trades.append(make_trade(candidate, scope, market, positions[market], row, float(row["close"]), "rank_exit_top_half_loss"))
                    del positions[market]
                else:
                    skip_reasons[market].add("open_position_missing_rebalance_row")

        top_positive = [(m, ret, row) for m, ret, row in ranking_rows[:3] if ret > 0]
        for market, _ret, row in top_positive:
            count_by_market[market]["raw_signals"] += 1
            if market in positions:
                count_by_market[market]["signals_while_position_or_exit"] += 1
                skip_reasons[market].add("already_open_top3")
                continue
            if len(positions) >= 3:
                count_by_market[market]["skipped_entries"] += 1
                skip_reasons[market].add("portfolio_max_positions")
                continue
            stop = float(row["close"]) - 2.0 * float(row["atr14"])
            if not math.isfinite(stop) or stop >= float(row["close"]):
                count_by_market[market]["invalid_stop_skips"] += 1
                skip_reasons[market].add("invalid_or_nonfinite_stop")
                continue
            count_by_market[market]["entry_candidates"] += 1
            positions[market] = {
                "entry_index": int(row["row_index"]),
                "entry_timestamp": pd.Timestamp(row["timestamp"]),
                "entry_price": float(row["close"]),
                "stop_price": stop,
                "size": FIXED_NOTIONAL / float(row["close"]),
            }

    for market in positions:
        count_by_market[market]["open_position_at_scope_end"] += 1
        count_by_market[market]["skipped_entries"] += 1
        skip_reasons[market].add("open_position_not_force_closed_at_scope_end")
    for market, counts in count_by_market.items():
        counts["skipped_entries"] += counts["invalid_stop_skips"] + counts["signals_while_position_or_exit"]
        counts["skip_reasons"] = "|".join(sorted(skip_reasons[market]))
    return trades, list(count_by_market.values())


def profit_factor(trades: list[Trade]) -> float | None:
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    if gross_loss > 0:
        return gross_profit / gross_loss
    if gross_profit > 0:
        return math.inf
    return None


def max_drawdown_pct(trades: list[Trade]) -> float:
    equity = STARTING_EQUITY
    peak = equity
    max_dd = 0.0
    for trade in sorted(trades, key=lambda item: (item.exit_timestamp, item.market, item.candidate)):
        equity += trade.pnl
        peak = max(peak, equity)
        if peak > 0:
            max_dd = min(max_dd, equity / peak - 1.0)
    return abs(max_dd) * 100.0


def metrics_for(trades: list[Trade]) -> dict[str, Any]:
    pnls = [t.pnl for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    holds = [t.hold_bars for t in trades]
    return {
        "trade_count": len(trades),
        "net_pnl": sum(pnls),
        "profit_factor": profit_factor(trades),
        "max_dd_pct": max_drawdown_pct(trades),
        "win_rate_pct": (len(wins) / len(trades) * 100.0) if trades else 0.0,
        "avg_trade": float(np.mean(pnls)) if pnls else None,
        "median_trade": float(np.median(pnls)) if pnls else None,
        "gross_profit": sum(wins),
        "gross_loss": abs(sum(losses)),
        "fee_burden": sum(t.commission for t in trades),
        "avg_hold_bars": float(np.mean(holds)) if holds else None,
        "median_hold_bars": float(np.median(holds)) if holds else None,
        "stop_loss_count": sum(1 for t in trades if "stop" in t.exit_reason),
        "time_stop_count": sum(1 for t in trades if "time_stop" in t.exit_reason),
    }


def metric_rows_by_market(candidate: str, scope: str, trades: list[Trade]) -> list[dict[str, Any]]:
    rows = []
    for market in MARKETS:
        subset = [t for t in trades if t.market == market]
        rows.append({"candidate": candidate, "scope": scope, "market": market, "family": family(market), **metrics_for(subset)})
    return rows


def metric_rows_by_family(candidate: str, scope: str, trades: list[Trade]) -> list[dict[str, Any]]:
    rows = []
    families = sorted(set(FAMILY_BY_MARKET.values()) | {"other"})
    for fam in families:
        subset = [t for t in trades if t.family == fam]
        rows.append({"candidate": candidate, "scope": scope, "family": fam, **metrics_for(subset)})
    return rows


def split_frames(data: dict[str, pd.DataFrame], scope: str) -> dict[str, pd.DataFrame]:
    return {market: df[df["scope"] == scope].copy() for market, df in data.items()}


def buy_hold_pnl(df: pd.DataFrame, notional: float) -> tuple[float | None, float | None, float | None, str, str]:
    if df.empty:
        return None, None, None, "", ""
    start = float(df.iloc[0]["close"])
    end = float(df.iloc[-1]["close"])
    if start <= 0:
        return None, start, end, df.iloc[0]["timestamp"].isoformat(), df.iloc[-1]["timestamp"].isoformat()
    return notional * (end / start - 1.0), start, end, df.iloc[0]["timestamp"].isoformat(), df.iloc[-1]["timestamp"].isoformat()


def decision_for(candidate: str, scope: str, metrics: dict[str, Any], market_rows: list[dict[str, Any]], passive_btc_pnl: float | None) -> tuple[str, str, str]:
    net = float(metrics["net_pnl"])
    pf = metrics["profit_factor"]
    trades = int(metrics["trade_count"])
    btc_row = next((row for row in market_rows if row["candidate"] == candidate and row["scope"] == scope and row["market"] == "BTCUSDT"), None)
    btc_trades = int(btc_row["trade_count"]) if btc_row else 0
    btc_net = float(btc_row["net_pnl"]) if btc_row else 0.0
    positive_markets = sum(1 for row in market_rows if row["candidate"] == candidate and row["scope"] == scope and float(row["net_pnl"]) > 0)
    top_conc = concentration_for(candidate, scope, [t for t in ALL_TRADES if t.candidate == candidate and t.scope == scope])["top3_pct_of_positive_market_pnl"]
    reasons: list[str] = []
    if net <= 0:
        reasons.append("aggregate_negative_or_no_edge")
    if pf is None or (not math.isinf(float(pf)) and float(pf) < 1.0):
        reasons.append("PF_below_1_or_NA")
    if net <= 0:
        reasons.append("no_trade_not_beaten")
    if passive_btc_pnl is not None and passive_btc_pnl > net:
        reasons.append("passive_BTC_dominates")
    if trades < 30:
        reasons.append("low_trade_count")
    if btc_trades > 0 and btc_net < 0:
        reasons.append("BTCUSDT_negative")
    if positive_markets < 5:
        reasons.append("weak_market_breadth")
    if top_conc not in {None, ""} and float(top_conc) > 80:
        reasons.append("high_market_concentration")
    hard_fail_reasons = [
        reason
        for reason in reasons
        if reason
        in {
            "aggregate_negative_or_no_edge",
            "PF_below_1_or_NA",
            "no_trade_not_beaten",
            "passive_BTC_dominates",
            "BTCUSDT_negative",
            "weak_market_breadth",
            "high_market_concentration",
        }
    ]
    if net > 0 and pf is not None and float(pf) >= 1.10 and trades >= 30 and (btc_trades == 0 or btc_net >= 0) and positive_markets >= 5 and not reasons:
        return "promising_for_confirmation", "pass", "all predeclared pass gates satisfied; still research-only"
    if hard_fail_reasons:
        return "fail", "fail", "|".join(reasons)
    if net > 0:
        return "caution", "caution", "|".join(reasons) if reasons else "positive_but_requires_confirmation"
    return "fail", "fail", "|".join(reasons)


def concentration_for(candidate: str, scope: str, trades: list[Trade]) -> dict[str, Any]:
    market_pnls = [(market, sum(t.pnl for t in trades if t.market == market)) for market in MARKETS]
    market_pnls.sort(key=lambda pair: pair[1], reverse=True)
    positive = [(m, pnl) for m, pnl in market_pnls if pnl > 0]
    positive_sum = sum(pnl for _m, pnl in positive)
    top3 = positive[:3]
    top5 = positive[:5]
    pos_trades = sorted([t.pnl for t in trades if t.pnl > 0], reverse=True)
    top10_sum = sum(pos_trades[:10])
    pos_trade_sum = sum(pos_trades)
    return {
        "candidate": candidate,
        "scope": scope,
        "aggregate_net_pnl": sum(pnl for _m, pnl in market_pnls),
        "positive_market_pnl_sum": positive_sum,
        "top_market": market_pnls[0][0] if market_pnls else "",
        "top_market_pnl": market_pnls[0][1] if market_pnls else 0.0,
        "top3_markets": "|".join(m for m, _p in top3),
        "top3_pnl": sum(p for _m, p in top3),
        "top3_pct_of_positive_market_pnl": (sum(p for _m, p in top3) / positive_sum * 100.0) if positive_sum else None,
        "top5_markets": "|".join(m for m, _p in top5),
        "top5_pnl": sum(p for _m, p in top5),
        "top5_pct_of_positive_market_pnl": (sum(p for _m, p in top5) / positive_sum * 100.0) if positive_sum else None,
        "top10_positive_trade_pnl": top10_sum,
        "top10_positive_trade_pct_of_positive_trade_pnl": (top10_sum / pos_trade_sum * 100.0) if pos_trade_sum else None,
        "positive_trade_pnl_sum": pos_trade_sum,
    }


def slippage_metrics(trades: list[Trade], extra_bps: float) -> dict[str, Any]:
    adjusted: list[float] = []
    gross_profit = 0.0
    gross_loss = 0.0
    for trade in trades:
        extra = (trade.entry_price + trade.exit_price) * trade.size * (extra_bps / 10000.0)
        pnl = trade.pnl - extra
        adjusted.append(pnl)
        if pnl > 0:
            gross_profit += pnl
        elif pnl < 0:
            gross_loss += abs(pnl)
    pf = gross_profit / gross_loss if gross_loss else (math.inf if gross_profit > 0 else None)
    return {
        "extra_slippage_bps_per_side": extra_bps,
        "trade_count": len(trades),
        "net_pnl": sum(adjusted),
        "profit_factor": pf,
        "avg_trade": float(np.mean(adjusted)) if adjusted else None,
    }


def output_float(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)) and math.isinf(float(value)):
        return "inf"
    return value


def clean_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: output_float(value) for key, value in row.items()} for row in rows]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    data = {market: load_market(market) for market in MARKETS}
    btc_regime = compute_btc_regime(data["BTCUSDT"])
    for market in MARKETS:
        data[market] = attach_btc_regime(data[market], btc_regime)

    all_trades: list[Trade] = []
    warmup_rows: list[dict[str, Any]] = []
    for scope in ["reference", "holdout"]:
        for candidate in [c for c in CANDIDATES if c != "B_cross_sectional_top3_round1"]:
            for market in MARKETS:
                trades, counts = simulate_market_candidate(candidate, market, data[market], scope)
                all_trades.extend(trades)
                warmup_rows.append(counts)
        b_trades, b_counts = simulate_b_candidate(data, scope)
        all_trades.extend(b_trades)
        warmup_rows.extend(b_counts)

    global ALL_TRADES
    ALL_TRADES = all_trades

    aggregate_rows: list[dict[str, Any]] = []
    market_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    exposure_rows: list[dict[str, Any]] = []
    for scope in ["reference", "holdout"]:
        scope_frames = split_frames(data, scope)
        total_market_bars = sum(len(frame) for frame in scope_frames.values())
        for candidate in CANDIDATES:
            trades = [t for t in all_trades if t.candidate == candidate and t.scope == scope]
            metrics = metrics_for(trades)
            candidate_market_rows = metric_rows_by_market(candidate, scope, trades)
            market_rows.extend(candidate_market_rows)
            family_rows.extend(metric_rows_by_family(candidate, scope, trades))
            positive_markets = sum(1 for row in candidate_market_rows if float(row["net_pnl"]) > 0)
            negative_markets = sum(1 for row in candidate_market_rows if float(row["net_pnl"]) < 0)
            hold_bars = sum(t.hold_bars for t in trades)
            exposure_pct = (hold_bars / total_market_bars * 100.0) if total_market_bars else 0.0
            aggregate_rows.append({
                "candidate": candidate,
                "family_id": FAMILY_BY_CANDIDATE[candidate],
                "scope": scope,
                "market_count": len(MARKETS),
                **metrics,
                "positive_market_count": positive_markets,
                "negative_market_count": negative_markets,
                "flat_market_count": len(MARKETS) - positive_markets - negative_markets,
                "exposure_bars": hold_bars,
                "available_market_bars": total_market_bars,
                "exposure_time_in_market_pct": exposure_pct,
            })
            exposure_rows.append({
                "candidate": candidate,
                "scope": scope,
                "trade_count": len(trades),
                "exposure_bars": hold_bars,
                "available_market_bars": total_market_bars,
                "exposure_time_in_market_pct": exposure_pct,
                "open_positions_not_force_closed": sum(int(row.get("open_position_at_scope_end", 0)) for row in warmup_rows if row["candidate"] == candidate and row["scope"] == scope),
                "notes": "Open positions at scope end are not force-closed, matching prior research script convention.",
            })

    # Passive BTC benchmark by scope, normalized to starting equity.
    passive_rows: list[dict[str, Any]] = []
    passive_by_scope: dict[str, float | None] = {}
    for scope in ["reference", "holdout"]:
        pnl, start, end, start_ts, end_ts = buy_hold_pnl(data["BTCUSDT"][data["BTCUSDT"]["scope"] == scope], STARTING_EQUITY)
        passive_by_scope[scope] = pnl
        for candidate in CANDIDATES:
            net = next(row["net_pnl"] for row in aggregate_rows if row["candidate"] == candidate and row["scope"] == scope)
            passive_rows.append({
                "candidate": candidate,
                "scope": scope,
                "passive_btc_start_timestamp": start_ts,
                "passive_btc_end_timestamp": end_ts,
                "passive_btc_start_close": start,
                "passive_btc_end_close": end,
                "passive_btc_normalized_notional": STARTING_EQUITY,
                "passive_btc_pnl": pnl,
                "candidate_net_pnl": net,
                "candidate_minus_passive_btc": (net - pnl) if pnl is not None else "",
                "interpretation": "passive_btc_dominates" if pnl is not None and pnl > net else "candidate_beats_passive_btc",
            })

    no_trade_rows = []
    for row in aggregate_rows:
        no_trade_rows.append({
            "candidate": row["candidate"],
            "scope": row["scope"],
            "candidate_net_pnl": row["net_pnl"],
            "no_trade_pnl": 0.0,
            "candidate_minus_no_trade": row["net_pnl"],
            "no_trade_preferred_by": abs(row["net_pnl"]) if row["net_pnl"] < 0 else 0.0,
            "candidate_beats_no_trade": row["net_pnl"] > 0,
        })

    buy_hold_rows: list[dict[str, Any]] = []
    buy_hold_aggregate_by_scope: dict[str, float] = {}
    for scope in ["reference", "holdout"]:
        scope_total = 0.0
        for market in MARKETS:
            pnl, start, end, start_ts, end_ts = buy_hold_pnl(data[market][data[market]["scope"] == scope], FIXED_NOTIONAL)
            if pnl is not None:
                scope_total += pnl
            for candidate in CANDIDATES:
                strategy_pnl = sum(t.pnl for t in all_trades if t.candidate == candidate and t.scope == scope and t.market == market)
                buy_hold_rows.append({
                    "candidate": candidate,
                    "scope": scope,
                    "market": market,
                    "buy_hold_start_timestamp": start_ts,
                    "buy_hold_end_timestamp": end_ts,
                    "buy_hold_start_close": start,
                    "buy_hold_end_close": end,
                    "buy_hold_notional": FIXED_NOTIONAL,
                    "buy_hold_pnl": pnl,
                    "strategy_market_pnl": strategy_pnl,
                    "strategy_minus_buy_hold": (strategy_pnl - pnl) if pnl is not None else "",
                })
        buy_hold_aggregate_by_scope[scope] = scope_total

    concentration_rows = []
    for scope in ["reference", "holdout"]:
        for candidate in CANDIDATES:
            concentration_rows.append(concentration_for(candidate, scope, [t for t in all_trades if t.candidate == candidate and t.scope == scope]))

    slippage_rows = []
    for scope in ["reference", "holdout"]:
        for candidate in CANDIDATES:
            trades = [t for t in all_trades if t.candidate == candidate and t.scope == scope]
            for bps in EXTRA_SLIPPAGE_BPS:
                slippage_rows.append({"candidate": candidate, "scope": scope, **slippage_metrics(trades, bps)})

    data_coverage_rows = []
    for market in MARKETS:
        df = data[market]
        deltas = df["timestamp"].sort_values().diff().dropna().dt.total_seconds() / 3600.0
        gaps = int((deltas > 4.0).sum())
        duplicates = int(len(df) - df["timestamp"].nunique())
        for scope in ["reference", "holdout"]:
            sdf = df[df["scope"] == scope]
            data_coverage_rows.append({
                "market": market,
                "family": family(market),
                "scope": scope,
                "source_path": f"data/{market}_4h.csv",
                "timeframe": "4h",
                "rows": len(sdf),
                "start_timestamp": sdf["timestamp"].min().isoformat() if not sdf.empty else "",
                "end_timestamp": sdf["timestamp"].max().isoformat() if not sdf.empty else "",
                "full_file_rows": len(df),
                "full_file_start": df["timestamp"].min().isoformat(),
                "full_file_end": df["timestamp"].max().isoformat(),
                "duplicate_timestamps": duplicates,
                "gap_count_gt_4h_full_file": gaps,
                "timezone": "UTC",
                "new_fetch_used": False,
                "excluded_data": "BTCUSDT_1h; funding; OI; taker-flow; basis; private/account/order data",
                "coverage_status": "usable_existing_local_4h_ohlcv" if len(sdf) else "missing_scope_rows",
            })

    key_rows = [row for row in market_rows if row["market"] in KEY_MARKETS]

    failed_refs = [
        {"reference_name": "Candidate D later-data failure", "scope": "later_fetched", "reference_net_pnl": -174.23466018511795, "reference_pf": 0.13132609206323043, "reference_status": "fail"},
        {"reference_name": "Funding-gated Candidate D failure", "scope": "later_fetched", "reference_net_pnl": -126.24, "reference_pf": 0.0, "reference_status": "fail"},
        {"reference_name": "Aggregate taker-flow gated failure", "scope": "later_fetched", "reference_net_pnl": 0.0, "reference_pf": None, "reference_status": "fail_zero_trades"},
        {"reference_name": "Autonomous loop best near-miss K", "scope": "holdout", "reference_net_pnl": 769.166224, "reference_pf": 1.084287, "reference_status": "failed_promotion_gates"},
        {"reference_name": "Long1-only failure chain", "scope": "historical", "reference_net_pnl": "", "reference_pf": "", "reference_status": "closed_not_implementation_ready"},
    ]
    failed_reference_rows = []
    for scope in ["reference", "holdout"]:
        for candidate in CANDIDATES:
            net = next(row["net_pnl"] for row in aggregate_rows if row["candidate"] == candidate and row["scope"] == scope)
            pf = next(row["profit_factor"] for row in aggregate_rows if row["candidate"] == candidate and row["scope"] == scope)
            for ref in failed_refs:
                ref_net = ref["reference_net_pnl"]
                failed_reference_rows.append({
                    "candidate": candidate,
                    "candidate_scope": scope,
                    "candidate_net_pnl": net,
                    "candidate_pf": pf,
                    **ref,
                    "candidate_minus_reference_net_pnl": (net - ref_net) if isinstance(ref_net, (int, float)) else "",
                    "notes": "Prior failed references are context only; beating a failed reference is not a pass gate.",
                })

    decisions = []
    for scope in ["reference", "holdout"]:
        for candidate in CANDIDATES:
            metrics = next(row for row in aggregate_rows if row["candidate"] == candidate and row["scope"] == scope)
            status, gate, reason = decision_for(candidate, scope, metrics, market_rows, passive_by_scope[scope])
            decisions.append({
                "candidate": candidate,
                "family_id": FAMILY_BY_CANDIDATE[candidate],
                "scope": scope,
                "decision": status,
                "gate_class": gate,
                "reason": reason,
                "implementation_readiness": "not_ready_research_only",
                "next_status_allowed": "needs_confirmation_plan" if status == "promising_for_confirmation" else "parked_or_postmortem",
            })

    holdout_decisions = {row["candidate"]: row for row in decisions if row["scope"] == "holdout"}
    decision_rank = {"promising_for_confirmation": 0, "caution": 1, "fail": 2}
    aggregate_by_candidate = {row["candidate"]: row for row in aggregate_rows if row["scope"] == "holdout"}
    concentration_by_candidate = {row["candidate"]: row for row in concentration_rows if row["scope"] == "holdout"}

    def ranking_key(candidate: str) -> tuple[Any, ...]:
        agg = aggregate_by_candidate[candidate]
        dec = holdout_decisions[candidate]["decision"]
        pf = agg["profit_factor"]
        pf_sort = float(pf) if pf not in {None, ""} and not (isinstance(pf, float) and math.isinf(pf)) else (-1.0 if pf is None else 999999.0)
        btc = next((row for row in key_rows if row["candidate"] == candidate and row["scope"] == "holdout" and row["market"] == "BTCUSDT"), None)
        conc = concentration_by_candidate[candidate]
        passive_delta = next(row["candidate_minus_passive_btc"] for row in passive_rows if row["candidate"] == candidate and row["scope"] == "holdout")
        return (
            decision_rank.get(dec, 99),
            -float(agg["net_pnl"]),
            -pf_sort,
            float(agg["max_dd_pct"]),
            -int(agg["positive_market_count"]),
            -float(btc["net_pnl"] if btc else 0.0),
            float(conc["top3_pct_of_positive_market_pnl"] or 999.0),
            -int(agg["trade_count"]),
            -float(passive_delta if passive_delta != "" else -999999.0),
            CANDIDATES.index(candidate),
        )

    ranked = sorted(CANDIDATES, key=ranking_key)
    ranking_rows = []
    for idx, candidate in enumerate(ranked, start=1):
        agg = aggregate_by_candidate[candidate]
        dec = holdout_decisions[candidate]
        conc = concentration_by_candidate[candidate]
        passive_delta = next(row["candidate_minus_passive_btc"] for row in passive_rows if row["candidate"] == candidate and row["scope"] == "holdout")
        ranking_rows.append({
            "rank": idx,
            "candidate": candidate,
            "family_id": FAMILY_BY_CANDIDATE[candidate],
            "decision": dec["decision"],
            "net_pnl": agg["net_pnl"],
            "profit_factor": agg["profit_factor"],
            "max_dd_pct": agg["max_dd_pct"],
            "positive_market_count": agg["positive_market_count"],
            "negative_market_count": agg["negative_market_count"],
            "BTCUSDT_net_pnl": next((row["net_pnl"] for row in key_rows if row["candidate"] == candidate and row["scope"] == "holdout" and row["market"] == "BTCUSDT"), 0.0),
            "top3_pct_of_positive_market_pnl": conc["top3_pct_of_positive_market_pnl"],
            "trade_count": agg["trade_count"],
            "candidate_minus_passive_btc": passive_delta,
            "ranking_notes": dec["reason"],
        })

    candidate_result_rows = []
    for scope in ["reference", "holdout"]:
        for candidate in CANDIDATES:
            agg = next(row for row in aggregate_rows if row["candidate"] == candidate and row["scope"] == scope)
            dec = next(row for row in decisions if row["candidate"] == candidate and row["scope"] == scope)
            rank = next((row["rank"] for row in ranking_rows if row["candidate"] == candidate), "") if scope == "holdout" else ""
            candidate_result_rows.append({
                "candidate": candidate,
                "family_id": FAMILY_BY_CANDIDATE[candidate],
                "candidate_name": CANDIDATE_NAMES[candidate],
                "scope": scope,
                "rank_if_holdout": rank,
                "decision": dec["decision"],
                **agg,
                "decision_reason": dec["reason"],
                "implementation_readiness": "not_ready_research_only",
            })

    ambiguity_rows = []
    plan_path = OUT / "first_pass_ohlcv_tournament_validation_plan_round1_frozen_rules_check.csv"
    plan_rows = list(csv.DictReader(plan_path.open("r", encoding="utf-8")))
    for row in plan_rows:
        if row["candidate_id"] in CANDIDATES:
            ambiguity_rows.append({
                "candidate": row["candidate_id"],
                "rule_component": row["rule_component"],
                "ambiguity_found_in_plan": row["ambiguity_found"],
                "plan_resolution_used": row["ambiguity_resolution"],
                "execution_allowed_without_approval_in_plan": row["execution_allowed_without_approval"],
                "validation_handling": "used_documented_minimum_non_optimized_resolution" if row["ambiguity_found"] else "used_frozen_rule_as_written",
                "new_threshold_added": False,
                "notes": row["notes"],
            })
    ambiguity_rows.append({
        "candidate": "B_cross_sectional_top3_round1",
        "rule_component": "rebalance_anchor",
        "ambiguity_found_in_plan": "yes_operational_anchor",
        "plan_resolution_used": "fixed 7-day cadence from first timestamp in each validation scope",
        "execution_allowed_without_approval_in_plan": "execution task approved plan ambiguity handling",
        "validation_handling": "non_optimized_calendar_anchor_no_threshold_sweep",
        "new_threshold_added": False,
        "notes": "Anchor affects calendar phasing only; no alternate anchors were tested.",
    })

    # Add aggregate buy-hold comparison rows.
    for scope in ["reference", "holdout"]:
        for candidate in CANDIDATES:
            strategy = next(row["net_pnl"] for row in aggregate_rows if row["candidate"] == candidate and row["scope"] == scope)
            buy_hold_rows.append({
                "candidate": candidate,
                "scope": scope,
                "market": "ALL_MARKETS_FIXED_NOTIONAL_SUM",
                "buy_hold_start_timestamp": "per_market_scope_start",
                "buy_hold_end_timestamp": "per_market_scope_end",
                "buy_hold_start_close": "",
                "buy_hold_end_close": "",
                "buy_hold_notional": FIXED_NOTIONAL * len(MARKETS),
                "buy_hold_pnl": buy_hold_aggregate_by_scope[scope],
                "strategy_market_pnl": strategy,
                "strategy_minus_buy_hold": strategy - buy_hold_aggregate_by_scope[scope],
            })

    # Write CSV outputs.
    write_csv(OUT / f"{PREFIX}_candidate_results.csv", clean_rows(candidate_result_rows))
    write_csv(OUT / f"{PREFIX}_aggregate_metrics.csv", clean_rows(aggregate_rows))
    write_csv(OUT / f"{PREFIX}_market_metrics.csv", clean_rows(market_rows))
    write_csv(OUT / f"{PREFIX}_key_market_metrics.csv", clean_rows(key_rows))
    write_csv(OUT / f"{PREFIX}_buy_hold_comparison.csv", clean_rows(buy_hold_rows))
    write_csv(OUT / f"{PREFIX}_no_trade_comparison.csv", clean_rows(no_trade_rows))
    write_csv(OUT / f"{PREFIX}_passive_btc_comparison.csv", clean_rows(passive_rows))
    write_csv(OUT / f"{PREFIX}_failed_reference_comparison.csv", clean_rows(failed_reference_rows))
    write_csv(OUT / f"{PREFIX}_tournament_ranking.csv", clean_rows(ranking_rows))
    write_csv(OUT / f"{PREFIX}_pass_fail_decision.csv", clean_rows(decisions))
    write_csv(OUT / f"{PREFIX}_concentration.csv", clean_rows(concentration_rows))
    write_csv(OUT / f"{PREFIX}_exposure.csv", clean_rows(exposure_rows))
    write_csv(OUT / f"{PREFIX}_fee_slippage_sensitivity.csv", clean_rows(slippage_rows))
    write_csv(OUT / f"{PREFIX}_data_coverage.csv", clean_rows(data_coverage_rows))
    write_csv(OUT / f"{PREFIX}_warmup_and_skips.csv", clean_rows(warmup_rows))
    write_csv(OUT / f"{PREFIX}_rule_ambiguity_handling.csv", clean_rows(ambiguity_rows))

    best = ranking_rows[0]
    promoted = [row for row in decisions if row["scope"] == "holdout" and row["decision"] == "promising_for_confirmation"]
    caution = [row for row in decisions if row["scope"] == "holdout" and row["decision"] == "caution"]
    failed = [row for row in decisions if row["scope"] == "holdout" and row["decision"] == "fail"]
    key_summary = []
    for market in KEY_MARKETS:
        vals = []
        for candidate in CANDIDATES:
            row = next(r for r in key_rows if r["candidate"] == candidate and r["scope"] == "holdout" and r["market"] == market)
            vals.append(f"{candidate}:{row['net_pnl']:.2f}/{row['trade_count']}tr")
        key_summary.append(f"{market} " + "; ".join(vals))

    note = f"""# First-Pass OHLCV Tournament Validation Round 1\n\nThis research-only validation executed the six predeclared OHLCV tournament candidates from `first_pass_ohlcv_tournament_validation_plan_round1` using existing local 4h OHLCV only. It did not fetch market data, run dry-run/live trading, modify production source, tune thresholds, create variants, or remove markets after results.\n\n## Data And Accounting\n\n- Markets: same 19 local 4h markets; BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remain visible.\n- Excluded data: BTCUSDT_1h, funding, OI, taker-flow, basis, private/account/order data.\n- Split: 70/30 chronological reference/holdout split per market. Holdout is the primary tournament decision scope.\n- Fees: 5 bps per side. Additional slippage sensitivity is reported separately.\n- Sizing: 1000 USDT fixed notional per trade/position, no leverage, no averaging down.\n\n## Holdout Result\n\n- Best ranked candidate: {best['candidate']} with decision `{best['decision']}`, net PnL {best['net_pnl']:.2f}, PF {best['profit_factor']}.\n- Promising for confirmation: {len(promoted)}.\n- Caution: {len(caution)}.\n- Fail: {len(failed)}.\n\nNo candidate is implementation-ready from this tournament. A pass, if present, only means `promising_for_confirmation` and requires separate confirmation planning before any further consideration.\n\n## Key Markets\n\n""" + "\n".join(f"- {line}" for line in key_summary) + "\n"
    (OUT / f"{PREFIX}_note.md").write_text(note, encoding="utf-8")

    limitations = """# Limitations\n\n- This is a first-pass research validation only, not an implementation or dry-run plan.\n- The validation used existing local 4h OHLCV only and did not fetch later/new data.\n- B/D/I operational ambiguity handling follows the committed validation plan and is documented in the ambiguity output; no alternate ambiguity resolutions were tested.\n- Open positions at scope end were not force-closed, matching prior research-script convention; open-position counts are reported in exposure and warmup/skip outputs.\n- Passive BTC and buy-and-hold comparisons are benchmarks, not trade recommendations.\n- Prior failed candidates are context only and cannot be revived by this tournament.\n"""
    (OUT / f"{PREFIX}_limitations.md").write_text(limitations, encoding="utf-8")

    handoff = f"""=== CHATGPT HANDOFF START ===\n1. run status: first_pass_ohlcv_tournament_validation_round1 executed as research-only validation; no fetch, dry-run/live, production change, threshold tuning, or market removal.\n2. branch / workspace state: research/long1-only-candidate-robustness; validation script/output generated locally pending commit.\n3. commands run: loaded frozen plans and source inventory, ran research/first_pass_ohlcv_tournament_validation_round1.py, generated required validation outputs and metrics.\n4. files changed / output paths: research/first_pass_ohlcv_tournament_validation_round1.py and research_output/first_pass_ohlcv_tournament_validation_round1_* outputs.\n5. candidates validated: {', '.join(CANDIDATES)}.\n6. rule ambiguity handling: B/D/I plan-marked ambiguities used documented non-optimized resolutions; no threshold sweeps or candidate variants were created.\n7. data scope used: existing local 4h OHLCV only; same 19 markets; BTC/DOGE/DOT/UNI visible; BTCUSDT_1h/funding/OI/taker/basis excluded.\n8. aggregate tournament results: best holdout candidate {best['candidate']} net PnL {best['net_pnl']:.2f}, PF {best['profit_factor']}, decision {best['decision']}.\n9. candidate ranking: {' > '.join(row['candidate'] for row in ranking_rows)}.\n10. pass/caution/fail decisions: pass {len(promoted)}, caution {len(caution)}, fail {len(failed)} on holdout.\n11. best candidate, if any: {best['candidate']} is best ranked; status {best['decision']} and still research-only.\n12. no-trade comparison: candidates with positive holdout PnL beat no-trade numerically; failed/caution gates still apply based on PF, breadth, BTC, concentration, and benchmark checks.\n13. passive BTC comparison: passive BTC benchmark reported for each candidate; passive BTC dominance is included in decision reasons.\n14. BTCUSDT / DOGE / DOT / UNI results: see key_market_metrics; {key_summary[0]}.\n15. concentration and breadth: concentration.csv and tournament_ranking.csv report market/trade concentration and positive/negative market breadth.\n16. data coverage / warmup / skip issues: data_coverage.csv and warmup_and_skips.csv report per-market coverage, gaps, warmup counts, skipped entries, and open positions not force-closed.\n17. what changed / did not change: added research script and research outputs only; no production source, parameters, deployment, PR, dry-run, live state, data fetch, or strategy definitions changed.\n18. implementation readiness judgment: not implementation-ready; no dry-run/live readiness claimed.\n19. commit / push result: pending at file creation time; verify final response for actual commit/push status.\n20. next recommended Codex prompt: Create a research-only postmortem/synthesis for first_pass_ohlcv_tournament_validation_round1, preserving no-trade as default unless a candidate passed all gates.\n21. one-sentence conclusion: The first-pass OHLCV tournament was executed under frozen rules and remains research-only with no implementation readiness.\n=== CHATGPT HANDOFF END ===\n"""
    (OUT / f"{PREFIX}_handoff.md").write_text(handoff, encoding="utf-8")

    expected = [
        "note.md",
        "candidate_results.csv",
        "aggregate_metrics.csv",
        "market_metrics.csv",
        "key_market_metrics.csv",
        "buy_hold_comparison.csv",
        "no_trade_comparison.csv",
        "passive_btc_comparison.csv",
        "failed_reference_comparison.csv",
        "tournament_ranking.csv",
        "pass_fail_decision.csv",
        "concentration.csv",
        "exposure.csv",
        "fee_slippage_sensitivity.csv",
        "data_coverage.csv",
        "warmup_and_skips.csv",
        "rule_ambiguity_handling.csv",
        "limitations.md",
        "handoff.md",
    ]
    missing = [name for name in expected if not (OUT / f"{PREFIX}_{name}").exists()]
    if missing:
        raise RuntimeError(f"missing output files: {missing}")
    print(f"wrote {len(expected)} output files")
    print(f"best_holdout={best['candidate']} decision={best['decision']} net={best['net_pnl']:.6f} pf={best['profit_factor']}")


if __name__ == "__main__":
    ALL_TRADES: list[Trade] = []
    main()
