#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.order_intent_writer_review import (
    build_writer_review_checklist,
    checklist_json,
    format_markdown_checklist,
    format_text_checklist,
    write_checklist_json,
    write_checklist_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only design review checklist for a future non-executing BTC OrderIntentWriter."
    )
    parser.add_argument(
        "--schema-path",
        default="schemas/btc_order_intent.schema.json",
        help="BTC order-intent schema path.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument("--output-json", default=None, help="Optional JSON checklist output path.")
    parser.add_argument("--output-md", default=None, help="Optional Markdown checklist output path.")
    parser.add_argument(
        "--include-future-test-plan",
        action="store_true",
        help="Include an extra future-only implementation sequence section.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
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
    schema_path = resolve_path(args.schema_path) or (ROOT / "schemas" / "btc_order_intent.schema.json")
    checklist = build_writer_review_checklist(
        schema_path=schema_path,
        include_future_test_plan=args.include_future_test_plan,
        strict=args.strict,
    )

    if args.output_json:
        output_json = resolve_path(args.output_json)
        write_checklist_json(checklist, output_json or Path(args.output_json))
    if args.output_md:
        output_md = resolve_path(args.output_md)
        write_checklist_markdown(checklist, output_md or Path(args.output_md))

    if args.format == "json":
        print(checklist_json(checklist), end="")
    else:
        print(format_text_checklist(checklist), end="")

    return 0 if checklist.safety_status in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
