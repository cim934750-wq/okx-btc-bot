from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

CSV_COLUMNS: tuple[str, ...] = ("timestamp", "open", "high", "low", "close", "volume")
NUMERIC_COLUMNS: tuple[str, ...] = ("open", "high", "low", "close", "volume")
OKX_PUBLIC_CANDLES_URL = "https://www.okx.com/api/v5/market/candles"
DEFAULT_INST_ID = "BTC-USDT"
DEFAULT_BAR = "4H"
FOUR_HOURS = timedelta(hours=4)


@dataclass(slots=True)
class DataRefreshReport:
    source: str
    output_path: str
    report_path: str | None
    old_rows: int
    new_rows: int
    old_latest_timestamp: str | None
    new_latest_timestamp: str | None
    fetched_rows: int
    complete_rows_kept: int
    incomplete_rows_excluded: int
    duplicate_rows_removed: int
    latest_candle_complete: bool
    gap_warnings: list[str]
    wrote_csv: bool
    error: str | None = None


def _utc_iso(timestamp: pd.Timestamp) -> str:
    return timestamp.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _parse_utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def _coerce_utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def validate_ohlcv_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in CSV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"OHLCV CSV missing required columns: {missing}")

    validated = frame[list(CSV_COLUMNS)].copy()
    validated["timestamp"] = pd.to_datetime(validated["timestamp"], utc=True, errors="coerce")
    if validated["timestamp"].isna().any():
        raise ValueError("OHLCV CSV contains invalid timestamps")

    for column in NUMERIC_COLUMNS:
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
    if validated[list(NUMERIC_COLUMNS)].isna().any().any():
        raise ValueError("OHLCV CSV contains non-numeric OHLCV values")
    if (validated["high"] < validated["low"]).any():
        raise ValueError("OHLCV CSV contains rows where high is lower than low")
    if (validated["volume"] < 0).any():
        raise ValueError("OHLCV CSV contains negative volume")

    return validated


def normalize_ohlcv_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    validated = validate_ohlcv_frame(frame)
    before = len(validated)
    normalized = (
        validated.sort_values("timestamp")
        .drop_duplicates("timestamp", keep="last")
        .reset_index(drop=True)
    )
    duplicates_removed = before - len(normalized)
    normalized["timestamp"] = normalized["timestamp"].map(_utc_iso)
    return normalized[list(CSV_COLUMNS)], duplicates_removed


def read_existing_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)
    return pd.read_csv(csv_path)


def latest_timestamp(frame: pd.DataFrame) -> str | None:
    if frame.empty or "timestamp" not in frame.columns:
        return None
    normalized, _ = normalize_ohlcv_frame(frame)
    if normalized.empty:
        return None
    return str(normalized["timestamp"].iloc[-1])


def _row_is_complete(row: list[Any], now: datetime | None, candle_delta: timedelta) -> bool:
    if len(row) >= 9:
        return str(row[8]) == "1"
    if not row:
        return False
    if now is None:
        return True
    opened_at = pd.to_datetime(int(row[0]), unit="ms", utc=True)
    now_ts = _coerce_utc_timestamp(now)
    return opened_at + candle_delta <= now_ts


def okx_rows_to_ohlcv_frame(
    rows: list[list[Any]],
    *,
    include_incomplete: bool = False,
    now: datetime | None = None,
) -> tuple[pd.DataFrame, int]:
    converted: list[dict[str, Any]] = []
    incomplete_excluded = 0
    for row in rows:
        if len(row) < 6:
            continue
        if not include_incomplete and not _row_is_complete(row, now, FOUR_HOURS):
            incomplete_excluded += 1
            continue
        timestamp = pd.to_datetime(int(row[0]), unit="ms", utc=True)
        converted.append(
            {
                "timestamp": _utc_iso(timestamp),
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
            }
        )

    if not converted:
        return pd.DataFrame(columns=CSV_COLUMNS), incomplete_excluded
    frame, _ = normalize_ohlcv_frame(pd.DataFrame(converted))
    return frame, incomplete_excluded


def merge_ohlcv_frames(existing: pd.DataFrame, fetched: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    merged_input = pd.concat([existing, fetched], ignore_index=True)
    return normalize_ohlcv_frame(merged_input)


def detect_time_gaps(frame: pd.DataFrame, expected_delta: timedelta = FOUR_HOURS) -> list[str]:
    if frame.empty:
        return []
    normalized = validate_ohlcv_frame(frame).sort_values("timestamp").reset_index(drop=True)
    deltas = normalized["timestamp"].diff().dropna()
    expected = pd.Timedelta(expected_delta)
    gap_positions = list(deltas[deltas > expected].index)
    warnings: list[str] = []
    for idx in gap_positions[:5]:
        previous_ts = normalized.loc[idx - 1, "timestamp"]
        current_ts = normalized.loc[idx, "timestamp"]
        warnings.append(
            f"Gap larger than 4h between {_utc_iso(previous_ts)} and {_utc_iso(current_ts)}."
        )
    if len(gap_positions) > 5:
        warnings.append(f"{len(gap_positions) - 5} additional gaps larger than 4h omitted from report.")
    return warnings


def fetch_okx_public_candles(
    *,
    inst_id: str = DEFAULT_INST_ID,
    bar: str = DEFAULT_BAR,
    limit: int = 300,
    timeout_seconds: float = 20.0,
) -> tuple[list[list[Any]], str]:
    query = urlencode({"instId": inst_id, "bar": bar, "limit": str(limit)})
    url = f"{OKX_PUBLIC_CANDLES_URL}?{query}"
    request = Request(url, headers={"User-Agent": "btc-signal-paper-refresh/1.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"OKX public candle fetch failed: {exc}") from exc

    if payload.get("code") != "0":
        raise RuntimeError(f"OKX public candle fetch failed: {payload.get('msg') or payload}")
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError("OKX public candle response did not contain a data list")
    return data, url


def write_refresh_report(report: DataRefreshReport, path: str | Path) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report.report_path = str(report_path)
    report_path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
    return report_path


def refresh_btcusdt_4h_csv(
    *,
    output_path: str | Path,
    report_path: str | Path | None = None,
    inst_id: str = DEFAULT_INST_ID,
    bar: str = DEFAULT_BAR,
    limit: int = 300,
    write_csv: bool = True,
    include_incomplete: bool = False,
    now: datetime | None = None,
) -> DataRefreshReport:
    target = Path(output_path)
    existing_raw = read_existing_csv(target)
    existing, existing_duplicates = normalize_ohlcv_frame(existing_raw) if not existing_raw.empty else (
        pd.DataFrame(columns=CSV_COLUMNS),
        0,
    )
    old_rows = len(existing)
    old_latest = latest_timestamp(existing)
    gap_warnings: list[str] = []

    rows, source = fetch_okx_public_candles(inst_id=inst_id, bar=bar, limit=limit)
    fetched, incomplete_excluded = okx_rows_to_ohlcv_frame(
        rows,
        include_incomplete=include_incomplete,
        now=now,
    )
    merged, merge_duplicates = merge_ohlcv_frames(existing, fetched)
    gap_warnings.extend(detect_time_gaps(merged))

    if write_csv:
        target.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(target, index=False)

    new_latest = latest_timestamp(merged)
    latest_complete = True
    if new_latest:
        latest_open = _parse_utc_timestamp(new_latest)
        now_ts = _coerce_utc_timestamp(now or datetime.now(timezone.utc))
        latest_complete = latest_open + pd.Timedelta(FOUR_HOURS) <= now_ts

    report = DataRefreshReport(
        source=source,
        output_path=str(target),
        report_path=str(report_path) if report_path is not None else None,
        old_rows=old_rows,
        new_rows=len(merged),
        old_latest_timestamp=old_latest,
        new_latest_timestamp=new_latest,
        fetched_rows=len(rows),
        complete_rows_kept=len(fetched),
        incomplete_rows_excluded=incomplete_excluded,
        duplicate_rows_removed=existing_duplicates + merge_duplicates,
        latest_candle_complete=latest_complete,
        gap_warnings=gap_warnings,
        wrote_csv=write_csv,
    )

    if report_path is not None:
        write_refresh_report(report, report_path)
    return report


def default_report_path(root: str | Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(root) / "runtime" / "data_refresh_reports" / f"btcusdt_4h_refresh_{stamp}.json"
