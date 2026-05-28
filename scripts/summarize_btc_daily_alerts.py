#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.alert_summary import (
    build_alert_summary,
    format_text_summary,
    summary_json,
    write_summary_json,
    write_summary_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize BTC paper daily-review alerts without external notifications or live trading."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--review-json", default=None, help="Daily review report JSON path.")
    source.add_argument("--snapshot-json", default=None, help="Daily review snapshot JSON path.")
    parser.add_argument("--compare-to", default=None, help="Optional prior snapshot/review JSON path.")
    parser.add_argument("--snapshot-dir", default="runtime/daily_reviews", help="Directory containing latest review files.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument("--output-json", default=None, help="Optional JSON alert summary output path.")
    parser.add_argument("--output-md", default=None, help="Optional Markdown alert summary output path.")
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
    review_json = resolve_path(args.review_json)
    snapshot_json = resolve_path(args.snapshot_json)
    compare_to = resolve_path(args.compare_to)
    snapshot_dir = resolve_path(args.snapshot_dir) or (ROOT / "runtime" / "daily_reviews")

    summary = build_alert_summary(
        review_json=review_json,
        snapshot_json=snapshot_json,
        snapshot_dir=snapshot_dir,
        compare_to=compare_to,
    )

    if args.output_json:
        output_json = resolve_path(args.output_json)
        write_summary_json(summary, output_json or Path(args.output_json))
    if args.output_md:
        output_md = resolve_path(args.output_md)
        write_summary_markdown(summary, output_md or Path(args.output_md))

    if args.format == "json":
        print(summary_json(summary))
    else:
        print(format_text_summary(summary), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
