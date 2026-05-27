#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from btc_signal.runner import build_parser, config_from_args, run_loop


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    cfg = config_from_args(args)
    run_loop(interval_seconds=args.interval_seconds, config=cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
