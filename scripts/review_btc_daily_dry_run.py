#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.config import BtcSignalConfig
from btc_signal.daily_review import (
    build_daily_review,
    format_text_review,
    review_json,
    write_review_json,
    write_review_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Archive and compare a read-only BTC paper daily dry-run status snapshot."
    )
    parser.add_argument("--data-path", default=None, help="BTCUSDT 4h CSV path.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--log-path", default=None, help="Single JSONL decision log path.")
    source.add_argument("--logs-dir", default=None, help="Directory containing btc_signal_decisions_*.jsonl logs.")
    parser.add_argument("--state-path", default=None, help="Paper state JSON path.")
    parser.add_argument("--snapshot-dir", default="runtime/daily_reviews", help="Directory for daily review snapshots.")
    parser.add_argument("--limit", type=int, default=20, help="Number of recent decision log entries to summarize.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument("--output-json", default=None, help="Optional full review JSON output path.")
    parser.add_argument("--output-md", default=None, help="Optional full review Markdown output path.")
    parser.add_argument("--compare-to", default=None, help="Optional prior snapshot JSON path to compare against.")
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
    data_path = resolve_path(args.data_path)
    if data_path is not None:
        cfg.data_path = data_path
    log_path = resolve_path(args.log_path)
    logs_dir = resolve_path(args.logs_dir) if args.logs_dir else cfg.log_dir
    state_path = resolve_path(args.state_path) if args.state_path else cfg.paper_state_path
    snapshot_dir = resolve_path(args.snapshot_dir) or (ROOT / "runtime" / "daily_reviews")
    compare_to = resolve_path(args.compare_to)

    review = build_daily_review(
        config=cfg,
        snapshot_dir=snapshot_dir,
        log_path=log_path,
        logs_dir=None if log_path is not None else logs_dir,
        state_path=state_path,
        limit=args.limit,
        compare_to=compare_to,
    )

    if args.output_md:
        output_md = resolve_path(args.output_md)
        write_review_markdown(review, output_md or Path(args.output_md))
    if args.output_json:
        output_json = resolve_path(args.output_json)
        write_review_json(review, output_json or Path(args.output_json))

    if args.format == "json":
        print(review_json(review))
    else:
        print(format_text_review(review), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
