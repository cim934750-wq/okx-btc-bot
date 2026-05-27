from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class BtcSignalConfig:
    symbol: str = "BTCUSDT"
    timeframe: str = "4h"
    root: Path = field(default_factory=Path.cwd)
    data_path: Path | None = None
    runtime_dir: Path | None = None
    paper_state_path: Path | None = None
    log_dir: Path | None = None
    stale_after_hours: float = 8.0
    max_exec_distance_atr: float = 2.75
    sudden_volatility_atr_ratio: float = 2.0
    sudden_volatility_step_ratio: float = 1.75
    min_atr_price_ratio: float = 0.0005
    signal_cooldown_hours: float = 12.0
    max_drawdown_allowed: float = 0.20

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        if self.data_path is None:
            self.data_path = self.root / "data" / "BTCUSDT_4h.csv"
        else:
            self.data_path = Path(self.data_path)
        if self.runtime_dir is None:
            self.runtime_dir = self.root / "runtime"
        else:
            self.runtime_dir = Path(self.runtime_dir)
        if self.paper_state_path is None:
            self.paper_state_path = self.runtime_dir / "paper_state.json"
        else:
            self.paper_state_path = Path(self.paper_state_path)
        if self.log_dir is None:
            self.log_dir = self.runtime_dir / "logs"
        else:
            self.log_dir = Path(self.log_dir)


def default_config(root: str | Path | None = None) -> BtcSignalConfig:
    return BtcSignalConfig(root=Path.cwd() if root is None else Path(root))
