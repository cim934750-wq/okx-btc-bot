from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.strategy import add_signal_columns


HEARTBEAT_PATH = ROOT / "logs" / "heartbeat.csv"
TRADES_PATH = ROOT / "logs" / "trades.csv"
PAPER_STATE_PATH = ROOT / "data" / "paper_state.json"
BOT_PATH = ROOT / "src" / "bot.py"
STRATEGY_PATH = ROOT / "src" / "strategy.py"
BACKTEST_PATH = ROOT / "research" / "backtest.py"
OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row and any(value not in {None, ""} for value in row.values())
        ]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str) and value == "":
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw in {None, ""}:
        return default
    try:
        return int(str(raw))
    except ValueError:
        return default


def parse_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw in {None, ""}:
        return default
    try:
        return float(str(raw))
    except ValueError:
        return default


def latest_non_empty(rows: list[dict[str, str]], column: str, default: str) -> str:
    for row in reversed(rows):
        value = row.get(column)
        if value:
            return value
    return default


def fetch_public_ohlcv(symbol: str, timeframe: str, limit: int) -> tuple[pd.DataFrame, Optional[str]]:
    try:
        import ccxt

        exchange = ccxt.okx(
            {
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )
        rows = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    except Exception as exc:  # noqa: BLE001 - diagnostics should degrade gracefully.
        return pd.DataFrame(), f"{exc.__class__.__name__}: {exc}"

    df = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    if df.empty:
        return df, "fetch returned no rows"

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    numeric_columns = ["open", "high", "low", "close", "volume"]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    return df, None


def signal_counts(heartbeat_rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in heartbeat_rows:
        counts[row.get("signal") or "missing"] += 1
    return counts


def trade_counts(trade_rows: list[dict[str, str]]) -> tuple[int, int, Counter[str]]:
    paper_rows = [
        row
        for row in trade_rows
        if (row.get("mode") or "").lower() == "paper" or row.get("dry_run") == "1"
    ]
    entries = sum(1 for row in paper_rows if row.get("action") == "entry")
    exits = sum(1 for row in paper_rows if row.get("action") == "exit")
    reasons = Counter(row.get("reason") or "missing" for row in paper_rows)
    return entries, exits, reasons


def max_consecutive_flat_exit_rows(heartbeat_rows: list[dict[str, str]]) -> int:
    longest = 0
    current = 0
    for row in heartbeat_rows:
        is_flat_exit = row.get("signal") == "exit" and not row.get("position_side")
        if is_flat_exit:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def code_level_checks() -> dict[str, bool]:
    bot_text = BOT_PATH.read_text(encoding="utf-8")
    strategy_text = STRATEGY_PATH.read_text(encoding="utf-8")
    backtest_text = BACKTEST_PATH.read_text(encoding="utf-8")
    return {
        "paper_stop_price_exit_present": (
            'close_paper_position(config, state, close, "stop_loss")' in bot_text
            and "close <= float(stop_price)" in bot_text
        ),
        "dry_run_uses_paper_decision": (
            "if config.dry_run:" in bot_text and "simulate_paper_decision" in bot_text
        ),
        "strategy_exit_is_close_below_ema20": (
            "if close < ema20:" in strategy_text
            and 'reason = "close_below_ema20"' in strategy_text
        ),
        "backtest_uses_strategy_exit_column": (
            "add_signal_columns" in backtest_text and 'row["exit"]' in backtest_text
        ),
    }


def condition_counts(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"ohlcv_rows": 0, "indicator_ready_rows": 0}

    data = add_signal_columns(df)
    ready = data.dropna(subset=["ema20", "ema60", "ema200", "rsi14", "atr14"]).copy()
    if ready.empty:
        return {"ohlcv_rows": len(data), "indicator_ready_rows": 0}

    close_gt_ema200 = ready["close"] > ready["ema200"]
    ema20_gt_ema60 = ready["ema20"] > ready["ema60"]
    rsi_between = ready["rsi14"].between(45, 70)
    long_entry = close_gt_ema200 & ema20_gt_ema60 & rsi_between
    close_lt_ema20 = ready["close"] < ready["ema20"]
    return {
        "ohlcv_rows": len(data),
        "indicator_ready_rows": len(ready),
        "close_gt_ema200": int(close_gt_ema200.sum()),
        "ema20_gt_ema60": int(ema20_gt_ema60.sum()),
        "rsi14_between_45_70": int(rsi_between.sum()),
        "all_long_entry_conditions": int(long_entry.sum()),
        "close_lt_ema20": int(close_lt_ema20.sum()),
        "long_entry_rate": float(long_entry.mean()),
        "exit_condition_rate": float(close_lt_ema20.mean()),
    }


def first_heartbeat_at_or_after(
    heartbeat_rows: list[dict[str, str]], timestamp: Optional[datetime]
) -> Optional[dict[str, str]]:
    if timestamp is None:
        return None
    for row in heartbeat_rows:
        row_timestamp = parse_timestamp(row.get("timestamp"))
        if row_timestamp is not None and row_timestamp >= timestamp:
            return row
    return None


def candle_timestamp(value: Any) -> Optional[pd.Timestamp]:
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed


def build_trade_segments(
    trade_rows: list[dict[str, str]], heartbeat_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    open_entry: Optional[dict[str, Any]] = None
    sorted_trades = sorted(
        trade_rows,
        key=lambda row: parse_timestamp(row.get("timestamp"))
        or datetime.min.replace(tzinfo=timezone.utc),
    )

    for row in sorted_trades:
        timestamp = parse_timestamp(row.get("timestamp"))
        action = row.get("action")
        if action == "entry":
            heartbeat = first_heartbeat_at_or_after(heartbeat_rows, timestamp)
            open_entry = {
                "entry_trade": row,
                "entry_time": timestamp,
                "entry_price": parse_float(row.get("price")),
                "entry_candle": heartbeat.get("candle_timestamp") if heartbeat else None,
            }
        elif action == "exit" and open_entry is not None:
            heartbeat = first_heartbeat_at_or_after(heartbeat_rows, timestamp)
            open_entry.update(
                {
                    "exit_trade": row,
                    "exit_time": timestamp,
                    "exit_price": parse_float(row.get("price")),
                    "exit_reason": row.get("reason") or "missing",
                    "exit_candle": heartbeat.get("candle_timestamp") if heartbeat else None,
                }
            )
            segments.append(open_entry)
            open_entry = None

    if open_entry is not None:
        segments.append(open_entry)
    return segments


def infer_stop_breaches(
    segments: list[dict[str, Any]],
    heartbeat_rows: list[dict[str, str]],
    ohlcv_with_indicators: pd.DataFrame,
    atr_stop_multiplier: float,
) -> dict[str, Any]:
    if not segments:
        return {
            "segments_checked": 0,
            "close_breach_segments": 0,
            "low_breach_segments": "unavailable",
            "details": [],
        }

    indicator_data = ohlcv_with_indicators.copy()
    if not indicator_data.empty:
        indicator_data["timestamp_key"] = pd.to_datetime(
            indicator_data["timestamp"], utc=True, errors="coerce"
        )

    details: list[str] = []
    close_breach_segments = 0
    low_breach_segments = 0
    low_available = not indicator_data.empty and "low" in indicator_data.columns
    checked = 0

    for index, segment in enumerate(segments, start=1):
        entry_price = segment.get("entry_price")
        entry_candle = candle_timestamp(segment.get("entry_candle"))
        if entry_price is None or entry_candle is None or indicator_data.empty:
            details.append(f"segment {index}: stop unavailable")
            continue

        entry_rows = indicator_data[indicator_data["timestamp_key"] == entry_candle]
        if entry_rows.empty:
            details.append(f"segment {index}: entry candle not in OHLCV")
            continue

        atr14 = parse_float(entry_rows.iloc[-1].get("atr14"))
        if atr14 is None:
            details.append(f"segment {index}: ATR14 unavailable")
            continue

        checked += 1
        stop_price = entry_price - (atr14 * atr_stop_multiplier)
        entry_time = segment.get("entry_time")
        exit_time = segment.get("exit_time")

        heartbeat_breach = False
        for row in heartbeat_rows:
            row_time = parse_timestamp(row.get("timestamp"))
            close = parse_float(row.get("close"))
            if row_time is None or close is None:
                continue
            if entry_time and row_time < entry_time:
                continue
            if exit_time and row_time > exit_time:
                continue
            if close <= stop_price:
                heartbeat_breach = True
                break

        if heartbeat_breach:
            close_breach_segments += 1

        low_breach = "unavailable"
        if low_available:
            exit_candle = candle_timestamp(segment.get("exit_candle"))
            mask = indicator_data["timestamp_key"] >= entry_candle
            if exit_candle is not None:
                mask &= indicator_data["timestamp_key"] <= exit_candle
            lows = indicator_data.loc[mask, "low"]
            low_breach = bool((lows <= stop_price).any()) if not lows.empty else False
            if low_breach:
                low_breach_segments += 1

        details.append(
            "segment {index}: entry={entry:.2f} inferred_stop={stop:.2f} "
            "exit_reason={reason} close_breached={close_breach} "
            "low_breached={low_breach}".format(
                index=index,
                entry=entry_price,
                stop=stop_price,
                reason=segment.get("exit_reason", "open"),
                close_breach=heartbeat_breach,
                low_breach=low_breach,
            )
        )

    return {
        "segments_checked": checked,
        "close_breach_segments": close_breach_segments,
        "low_breach_segments": low_breach_segments if low_available else "unavailable",
        "details": details,
    }


def classify_strategy(condition_summary: dict[str, Any], flat_exit_count: int, trade_entries: int) -> str:
    ready_rows = int(condition_summary.get("indicator_ready_rows") or 0)
    if ready_rows == 0:
        return "unknown: OHLCV indicators were unavailable"

    long_rate = float(condition_summary.get("long_entry_rate") or 0.0)
    exit_rate = float(condition_summary.get("exit_condition_rate") or 0.0)
    notes: list[str] = []

    if long_rate < 0.05:
        notes.append("entry side looks restrictive")
    elif long_rate > 0.35:
        notes.append("entry side may be permissive")
    else:
        notes.append("entry side looks moderate by raw candle frequency")

    if exit_rate > 0.45:
        notes.append("exit condition appears very frequent")
    elif exit_rate < 0.10:
        notes.append("exit condition appears uncommon")
    else:
        notes.append("exit condition frequency is moderate")

    if flat_exit_count > max(5, trade_entries):
        notes.append("runtime is repeatedly logging exit while flat")

    return "; ".join(notes)


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> None:
    load_dotenv(ROOT / ".env")
    heartbeat_rows = read_csv_rows(HEARTBEAT_PATH)
    trade_rows = read_csv_rows(TRADES_PATH)
    paper_state = read_json(PAPER_STATE_PATH)

    symbol = latest_non_empty(heartbeat_rows, "symbol", os.getenv("SYMBOL", "BTC/USDT"))
    timeframe = latest_non_empty(heartbeat_rows, "timeframe", os.getenv("TIMEFRAME", "1h"))
    candle_limit = max(300, parse_int_env("CANDLE_LIMIT", 300))
    atr_stop_multiplier = parse_float_env("ATR_STOP_MULTIPLIER", 2.0)

    ohlcv, fetch_error = fetch_public_ohlcv(symbol, timeframe, candle_limit)
    ohlcv_with_indicators = add_signal_columns(ohlcv) if not ohlcv.empty else pd.DataFrame()
    conditions = condition_counts(ohlcv)
    counts = signal_counts(heartbeat_rows)
    entries, exits, trade_reasons = trade_counts(trade_rows)
    checks = code_level_checks()
    flat_exit_rows = [
        row for row in heartbeat_rows if row.get("signal") == "exit" and not row.get("position_side")
    ]
    flat_exit_streak = max_consecutive_flat_exit_rows(heartbeat_rows)
    segments = build_trade_segments(trade_rows, heartbeat_rows)
    stop_breaches = infer_stop_breaches(
        segments,
        heartbeat_rows,
        ohlcv_with_indicators,
        atr_stop_multiplier,
    )

    print("Strategy Diagnostics")
    print(f"heartbeat_path: {HEARTBEAT_PATH}")
    print(f"trades_path: {TRADES_PATH}")
    print(f"paper_state_path: {PAPER_STATE_PATH}")
    print(f"symbol/timeframe: {symbol} / {timeframe}")

    print_section("Code-Level Checks")
    print(f"paper stop_price exit present: {checks['paper_stop_price_exit_present']}")
    print(f"dry-run uses paper decision path: {checks['dry_run_uses_paper_decision']}")
    print(f"strategy signal exit is close < EMA20: {checks['strategy_exit_is_close_below_ema20']}")
    print(f"backtest uses strategy exit column: {checks['backtest_uses_strategy_exit_column']}")
    print("paper exits can be stop_loss or close_below_ema20; strategy-generated exits are close_below_ema20")

    print_section("Runtime Logs")
    print(f"total heartbeat rows: {len(heartbeat_rows)}")
    print(f"signal count hold: {counts.get('hold', 0)}")
    print(f"signal count long_entry: {counts.get('long_entry', 0)}")
    print(f"signal count exit: {counts.get('exit', 0)}")
    other_signals = {key: value for key, value in counts.items() if key not in {"hold", "long_entry", "exit"}}
    print(f"other signal counts: {other_signals}")
    print(f"actual paper trade entries: {entries}")
    print(f"actual paper trade exits: {exits}")
    print(f"paper trade reasons: {dict(trade_reasons)}")

    print_section("Current Paper State")
    print(f"current position: {paper_state.get('current_simulated_position')}")
    print(f"entry price: {paper_state.get('entry_price')}")
    print(f"stop price: {paper_state.get('stop_price')}")
    print(f"final realized PnL: {paper_state.get('realized_pnl')}")
    print(f"final unrealized PnL: {paper_state.get('unrealized_pnl')}")

    print_section("OHLCV Condition Counts")
    if fetch_error:
        print(f"OHLCV fetch warning: {fetch_error}")
    print(f"OHLCV rows: {conditions.get('ohlcv_rows', 0)}")
    print(f"indicator-ready candles: {conditions.get('indicator_ready_rows', 0)}")
    print(f"candles close > EMA200: {conditions.get('close_gt_ema200', 0)}")
    print(f"candles EMA20 > EMA60: {conditions.get('ema20_gt_ema60', 0)}")
    print(f"candles RSI14 between 45 and 70: {conditions.get('rsi14_between_45_70', 0)}")
    print(f"candles meeting all long_entry conditions: {conditions.get('all_long_entry_conditions', 0)}")
    print(f"candles close < EMA20: {conditions.get('close_lt_ema20', 0)}")

    print_section("Stop Diagnostics")
    stop_loss_exits = sum(1 for row in trade_rows if row.get("reason") == "stop_loss")
    print(f"paper stop_loss exits logged: {stop_loss_exits}")
    print(f"segments checked with inferred stop: {stop_breaches['segments_checked']}")
    print(f"segments where heartbeat close breached inferred stop: {stop_breaches['close_breach_segments']}")
    print(f"segments where candle low breached inferred stop: {stop_breaches['low_breach_segments']}")
    for detail in stop_breaches["details"]:
        print(f"- {detail}")

    print_section("Repeated Flat Exit Diagnostics")
    print(f"no-position + signal=exit rows: {len(flat_exit_rows)}")
    print(f"max consecutive no-position + signal=exit streak: {flat_exit_streak}")
    print(f"repeated flat exits present: {len(flat_exit_rows) > 1}")

    print_section("Restrictive vs Permissive")
    print(classify_strategy(conditions, len(flat_exit_rows), entries))
    print("sample size note: current trade history is small, so treat this as diagnostic, not optimization")

    print_section("Candidate Improvements To Test Later")
    print("- EMA200 slope filter")
    print("- anti-chase filter using distance from EMA20 / ATR14")
    print("- cooldown after exit")
    print("- ATR trailing stop")
    print("- confirmed exit requiring 2 candle closes below EMA20")


if __name__ == "__main__":
    main()
