from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BINANCE_BASE_URL = "https://api.binance.com/api/v3/klines"
BYBIT_BASE_URL = "https://api.bybit.com/v5/market/kline"
FOUR_HOURS_MS = 4 * 60 * 60 * 1000


def _http_get_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _iso_utc_from_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()


def fetch_binance_4h(symbol: str, start_ms: int, end_ms: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cursor = start_ms

    while cursor < end_ms:
        query = urllib.parse.urlencode(
            {
                "symbol": symbol,
                "interval": "4h",
                "limit": 1000,
                "startTime": cursor,
                "endTime": end_ms,
            }
        )
        payload = _http_get_json(f"{BINANCE_BASE_URL}?{query}")
        if not isinstance(payload, list):
            raise RuntimeError(f"Unexpected Binance response: {payload}")
        if not payload:
            break

        for candle in payload:
            open_time = int(candle[0])
            rows.append(
                {
                    "timestamp": _iso_utc_from_ms(open_time),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }
            )

        last_open_time = int(payload[-1][0])
        next_cursor = last_open_time + FOUR_HOURS_MS
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        time.sleep(0.1)

    return rows


def fetch_bybit_4h(symbol: str, start_ms: int, end_ms: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    cursor_end = end_ms

    while cursor_end > start_ms:
        query = urllib.parse.urlencode(
            {
                "category": "linear",
                "symbol": symbol,
                "interval": "240",
                "limit": 1000,
                "end": cursor_end,
            }
        )
        payload = _http_get_json(f"{BYBIT_BASE_URL}?{query}")
        if not isinstance(payload, dict) or payload.get("retCode") != 0:
            raise RuntimeError(f"Unexpected Bybit response: {payload}")

        data = payload.get("result", {}).get("list", [])
        if not data:
            break

        for candle in data:
            open_time = int(candle[0])
            if open_time < start_ms or open_time > end_ms:
                continue
            rows.append(
                {
                    "timestamp": _iso_utc_from_ms(open_time),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }
            )

        oldest_open_time = min(int(candle[0]) for candle in data)
        next_end = oldest_open_time - 1
        if next_end >= cursor_end:
            break
        cursor_end = next_end
        time.sleep(0.1)

    rows.sort(key=lambda item: item["timestamp"])
    return rows


def deduplicate_and_sort(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[str, dict[str, object]] = {}
    for row in rows:
        deduped[str(row["timestamp"])] = row
    return [deduped[key] for key in sorted(deduped.keys())]


def save_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download BTCUSDT 4H OHLCV data.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--start", default="2019-01-01T00:00:00Z")
    parser.add_argument("--output", default="data/BTCUSDT_4h.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    start_dt = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    errors: list[str] = []
    rows: list[dict[str, object]] = []

    try:
        rows = fetch_binance_4h(args.symbol, start_ms, end_ms)
    except Exception as exc:  # pragma: no cover
        errors.append(f"Binance failed: {exc}")

    if not rows:
        try:
            rows = fetch_bybit_4h(args.symbol, start_ms, end_ms)
        except Exception as exc:  # pragma: no cover
            errors.append(f"Bybit failed: {exc}")

    rows = deduplicate_and_sort(rows)
    if not rows:
        raise RuntimeError("Failed to download data. " + " | ".join(errors))

    save_csv(rows, output_path)
    print(f"Saved {len(rows)} rows to {output_path}")
    print(f"First timestamp: {rows[0]['timestamp']}")
    print(f"Last timestamp: {rows[-1]['timestamp']}")


if __name__ == "__main__":
    main()
