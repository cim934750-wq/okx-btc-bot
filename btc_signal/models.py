from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class SignalAction(str, Enum):
    WAIT = "WAIT"
    WATCH = "WATCH"
    LONG_SIGNAL = "LONG_SIGNAL"
    BLOCKED = "BLOCKED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCK = "BLOCK"


class ResponseAction(str, Enum):
    WAIT = "WAIT"
    WATCH = "WATCH"
    PAPER_LONG = "PAPER_LONG"
    BLOCK = "BLOCK"
    EXIT_WARNING = "EXIT_WARNING"


@dataclass(slots=True)
class SignalDecision:
    timestamp: str | None
    symbol: str
    timeframe: str
    decision: str
    signal_name: str | None
    evidence: dict[str, Any]
    missing_conditions: list[str]
    passed_conditions: list[str]
    confidence_label: str
    reasoning_summary: str


@dataclass(slots=True)
class RiskAssessment:
    risk_level: str
    risk_flags: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ResponseDecision:
    action: str
    reason: str
    required_user_action: str | None
    should_log: bool = True
    should_notify: bool = False


@dataclass(slots=True)
class PaperState:
    symbol: str = "BTCUSDT"
    position_side: str | None = None
    entry_time: str | None = None
    entry_price: float | None = None
    last_signal_time: str | None = None
    paper_equity: float = 100_000.0
    max_drawdown_seen: float = 0.0
    open_position: bool = False
    notes: list[str] = field(default_factory=list)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value
