#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.config import BtcSignalConfig
from btc_signal.monitoring import (
    build_monitoring_report,
    format_text_report,
    monitoring_json,
    write_json_report,
    write_markdown_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize BTC paper/dry-run signal logs and paper state without live trading."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--log-path", default=None, help="Single JSONL decision log path.")
    source.add_argument("--logs-dir", default=None, help="Directory containing btc_signal_decisions_*.jsonl logs.")
    parser.add_argument("--state-path", default=None, help="Paper state JSON path.")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent valid log entries to summarize.")
    parser.add_argument("--output-json", default=None, help="Optional JSON report output path.")
    parser.add_argument("--output-md", default=None, help="Optional Markdown report output path.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument("--print-json", action="store_true", help="Print JSON output. Equivalent to --format json.")
    parser.add_argument(
        "--log-stale-after-hours",
        type=float,
        default=24.0,
        help="Warn when the latest decision log run_at is older than this many hours.",
    )
    return parser


def resolve_path(path_text: str | None) -> Path | None:
    if path_text is None:
        return None
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path


def main() -> int:
    args = build_parser().parse_args()
    cfg = BtcSignalConfig(root=ROOT)
    log_path = resolve_path(args.log_path)
    logs_dir = resolve_path(args.logs_dir) if args.logs_dir else cfg.log_dir
    state_path = resolve_path(args.state_path) if args.state_path else cfg.paper_state_path

    report = build_monitoring_report(
        log_path=log_path,
        logs_dir=None if log_path is not None else logs_dir,
        state_path=state_path,
        limit=args.limit,
        log_stale_after_hours=args.log_stale_after_hours,
    )

    if args.output_json:
        write_json_report(report, resolve_path(args.output_json) or Path(args.output_json))
    if args.output_md:
        write_markdown_report(report, resolve_path(args.output_md) or Path(args.output_md))

    if args.print_json or args.format == "json":
        print(monitoring_json(report))
    else:
        print(format_text_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
