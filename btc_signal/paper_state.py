from __future__ import annotations

import json
from pathlib import Path

from btc_signal.models import PaperState, SignalDecision, to_jsonable


def load_paper_state(path: str | Path, symbol: str = "BTCUSDT") -> PaperState:
    state_path = Path(path)
    if not state_path.exists():
        return PaperState(symbol=symbol, notes=["Initialized local paper state. No exchange orders are enabled."])
    payload = json.loads(state_path.read_text())
    payload.setdefault("symbol", symbol)
    payload.setdefault("notes", [])
    return PaperState(**payload)


def save_paper_state(state: PaperState, path: str | Path) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(to_jsonable(state), indent=2, sort_keys=True) + "\n")


def record_paper_long(state: PaperState, signal: SignalDecision) -> PaperState:
    close_value = signal.evidence.get("close")
    entry_price = float(close_value) if close_value is not None else None
    state.position_side = "LONG"
    state.entry_time = signal.timestamp
    state.entry_price = entry_price
    state.last_signal_time = signal.timestamp
    state.open_position = True
    state.notes.append("PAPER_LONG recorded locally only; no live exchange order was sent.")
    return state
