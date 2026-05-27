from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btc_signal.models import to_jsonable


def concise_json(payload: dict[str, Any]) -> str:
    return json.dumps(to_jsonable(payload), indent=2, sort_keys=True)


def write_decision_log(payload: dict[str, Any], log_dir: str | Path) -> Path:
    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = target_dir / f"btc_signal_decisions_{day}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(to_jsonable(payload), sort_keys=True) + "\n")
    return path
