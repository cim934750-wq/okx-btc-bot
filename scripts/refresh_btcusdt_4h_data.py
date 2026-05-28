#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.data_refresh import default_report_path, refresh_btcusdt_4h_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh local BTCUSDT 4h paper-mode OHLCV data from OKX public candles."
    )
    parser.add_argument("--output", default="data/BTCUSDT_4h.csv", help="CSV output path.")
    parser.add_argument("--report", default=None, help="Optional JSON report path.")
    parser.add_argument("--inst-id", default="BTC-USDT", help="OKX public instrument id.")
    parser.add_argument("--bar", default="4H", help="OKX candle bar.")
    parser.add_argument("--limit", type=int, default=300, help="Recent public candles to fetch.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and validate without writing CSV.")
    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Keep exchange-reported incomplete candles. Default excludes them.",
    )
    return parser


def resolve_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path


def main() -> int:
    args = build_parser().parse_args()
    output_path = resolve_path(args.output)
    report_path = resolve_path(args.report) if args.report else default_report_path(ROOT)
    try:
        report = refresh_btcusdt_4h_csv(
            output_path=output_path,
            report_path=report_path,
            inst_id=args.inst_id,
            bar=args.bar,
            limit=args.limit,
            write_csv=not args.dry_run,
            include_incomplete=args.include_incomplete,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should produce a report even on public fetch failure.
        failure_report = {
            "source": "OKX public market candles",
            "output_path": str(output_path),
            "report_path": str(report_path),
            "wrote_csv": False,
            "error": str(exc),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(failure_report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(failure_report, indent=2, sort_keys=True))
        return 1

    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
