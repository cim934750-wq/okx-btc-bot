#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.operator_checklist import (
    build_operator_checklist,
    checklist_json,
    format_text_checklist,
    write_checklist_json,
    write_checklist_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a read-only BTC paper-mode operator checklist for INFO/WARN/BLOCKED alert states."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--alert-json", default=None, help="Local alert summary JSON path.")
    source.add_argument("--review-json", default=None, help="Daily review report JSON path used to build an alert summary.")
    parser.add_argument("--snapshot-dir", default="runtime/daily_reviews", help="Directory containing daily review/alert files.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument("--output-json", default=None, help="Optional JSON checklist output path.")
    parser.add_argument("--output-md", default=None, help="Optional Markdown checklist output path.")
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
    alert_json = resolve_path(args.alert_json)
    review_json = resolve_path(args.review_json)
    snapshot_dir = resolve_path(args.snapshot_dir) or (ROOT / "runtime" / "daily_reviews")

    checklist = build_operator_checklist(
        alert_json=alert_json,
        review_json=review_json,
        snapshot_dir=snapshot_dir,
    )

    if args.output_json:
        output_json = resolve_path(args.output_json)
        write_checklist_json(checklist, output_json or Path(args.output_json))
    if args.output_md:
        output_md = resolve_path(args.output_md)
        write_checklist_markdown(checklist, output_md or Path(args.output_md))

    if args.format == "json":
        print(checklist_json(checklist))
    else:
        print(format_text_checklist(checklist), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
