#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.order_intent_schema_audit import (
    audit_json,
    audit_schema,
    format_text_audit,
    write_audit_json,
    write_audit_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only audit of the BTC non-executing order-intent JSON schema."
    )
    parser.add_argument(
        "--schema-path",
        default="schemas/btc_order_intent.schema.json",
        help="BTC order-intent schema path.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Terminal output format.")
    parser.add_argument("--output-json", default=None, help="Optional JSON audit output path.")
    parser.add_argument("--output-md", default=None, help="Optional Markdown audit output path.")
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
    audit = audit_schema(schema_path)

    if args.output_json:
        output_json = resolve_path(args.output_json)
        write_audit_json(audit, output_json or Path(args.output_json))
    if args.output_md:
        output_md = resolve_path(args.output_md)
        write_audit_markdown(audit, output_md or Path(args.output_md))

    if args.format == "json":
        print(audit_json(audit), end="")
    else:
        print(format_text_audit(audit), end="")

    return 0 if audit.safety_status in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
