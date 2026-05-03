from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_SYMBOL = "BTC/USDT"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_LIMIT = 1000
DEFAULT_MAX_CANDLES = 1000
DEFAULT_OUTPUT = "data/BTCUSDT_1h.csv"
CSV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download public OKX OHLCV candles for research/backtesting."
    )
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Market symbol, e.g. BTC/USDT.")
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME, help="Candle timeframe, e.g. 1h.")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Backward-compatible target candles when --max-candles is not set.",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Start timestamp, e.g. 2024-01-01T00:00:00Z. Defaults to recent candles.",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="Optional end timestamp, e.g. 2026-01-01T00:00:00Z. Defaults to now.",
    )
    parser.add_argument(
        "--max-candles",
        type=int,
        default=None,
        help="Maximum candles to save, e.g. 20000.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output CSV path, e.g. data/BTCUSDT_1h.csv.",
    )
    return parser.parse_args()


def resolve_output(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path


def timeframe_ms(exchange, timeframe: str) -> int:
    try:
        seconds = exchange.parse_timeframe(timeframe)
    except Exception as exc:  # noqa: BLE001 - produce a clearer CLI error.
        raise ValueError(f"Unsupported timeframe {timeframe!r}") from exc
    if seconds <= 0:
        raise ValueError(f"Unsupported timeframe {timeframe!r}")
    return int(seconds * 1000)


def parse_timestamp_ms(value: Optional[str], *, default_ms: Optional[int] = None) -> Optional[int]:
    if value in {None, ""}:
        return default_ms
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return int(timestamp.timestamp() * 1000)


def build_exchange():
    try:
        import ccxt
    except ImportError as exc:
        raise SystemExit(
            "ccxt is required. Install project dependencies with: pip install -r requirements.txt"
        ) from exc

    return ccxt.okx(
        {
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        }
    )


def dedupe_sort_rows(rows: Iterable[list[float]]) -> list[list[float]]:
    by_timestamp: dict[int, list[float]] = {}
    for row in rows:
        if not row:
            continue
        timestamp = int(row[0])
        by_timestamp[timestamp] = row[:6]
    return [by_timestamp[timestamp] for timestamp in sorted(by_timestamp)]


def fetch_ohlcv(
    exchange,
    symbol: str,
    timeframe: str,
    *,
    since_text: Optional[str],
    until_text: Optional[str],
    max_candles: int,
) -> tuple[list[list[float]], str]:
    if max_candles < 1:
        raise ValueError("--max-candles/--limit must be at least 1")

    exchange.load_markets()
    if symbol not in exchange.markets:
        raise ValueError(f"Symbol {symbol!r} is not available on OKX public markets")

    candle_ms = timeframe_ms(exchange, timeframe)
    now_ms = exchange.milliseconds()
    until_ms = parse_timestamp_ms(until_text, default_ms=now_ms)
    if until_ms is None:
        until_ms = now_ms
    if until_ms > now_ms:
        until_ms = now_ms

    request_limit = min(max(max_candles, 1), 300)
    if since_text:
        since = parse_timestamp_ms(since_text)
    else:
        lookback_candles = max_candles + request_limit + 10
        since = until_ms - (lookback_candles * candle_ms)
    if since is None:
        raise ValueError("--since could not be parsed")
    if since >= until_ms:
        raise ValueError("--since must be earlier than --until")

    all_rows: list[list[float]] = []
    stop_reason = "no more data"

    while True:
        unique_rows = dedupe_sort_rows(all_rows)
        if len(unique_rows) >= max_candles:
            stop_reason = "max_candles reached"
            break
        if since >= until_ms:
            stop_reason = "until reached"
            break

        remaining = max_candles - len(unique_rows)
        batch_limit = min(request_limit, remaining)
        batch = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=batch_limit,
        )
        if not batch:
            stop_reason = "no more data"
            break

        filtered_batch = [row for row in batch if int(row[0]) < until_ms]
        all_rows.extend(filtered_batch)
        unique_rows = dedupe_sort_rows(all_rows)
        if not filtered_batch or not unique_rows:
            stop_reason = "until reached"
            break

        last_timestamp = int(max(row[0] for row in filtered_batch))
        next_since = last_timestamp + candle_ms
        if next_since <= since:
            stop_reason = "no more data"
            break
        since = next_since

        if len(unique_rows) >= max_candles:
            stop_reason = "max_candles reached"
            break
        if since >= until_ms:
            stop_reason = "until reached"
            break
        if len(batch) < batch_limit:
            stop_reason = "no more data"
            break
        if getattr(exchange, "enableRateLimit", False):
            sleep_ms = getattr(exchange, "rateLimit", 0) or 0
            if sleep_ms > 0:
                exchange.sleep(sleep_ms)

    rows = dedupe_sort_rows(all_rows)
    return rows[:max_candles], stop_reason


def rows_to_dataframe(rows: list[list[float]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    if df.empty:
        return df
    numeric_columns = ["open", "high", "low", "close", "volume"]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return df[CSV_COLUMNS]


def save_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


def main() -> None:
    args = parse_args()
    output_path = resolve_output(args.output)
    exchange = build_exchange()
    max_candles = args.max_candles if args.max_candles is not None else args.limit
    rows, stop_reason = fetch_ohlcv(
        exchange,
        args.symbol,
        args.timeframe,
        since_text=args.since,
        until_text=args.until,
        max_candles=max_candles,
    )
    df = rows_to_dataframe(rows)
    save_csv(df, output_path)

    first_timestamp = df["timestamp"].iloc[0] if not df.empty else "n/a"
    last_timestamp = df["timestamp"].iloc[-1] if not df.empty else "n/a"
    print(f"candles saved: {len(df)}")
    print(f"first timestamp: {first_timestamp}")
    print(f"last timestamp: {last_timestamp}")
    print(f"output path: {output_path}")
    print(f"stopped because: {stop_reason}")


if __name__ == "__main__":
    main()
