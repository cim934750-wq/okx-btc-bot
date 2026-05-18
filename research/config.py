from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class BacktestConfig:
    initial_cash: float = 100_000.0
    commission: float = 0.0005
    starter_size: float = 0.01
    add_on_size: float = 0.005
    allow_longs: bool = True
    allow_shorts: bool = True
    enable_add_on_entries: bool = True
    partial_exit_pct: float = 0.50
    trade_on_close: bool = True
    exclusive_orders: bool = False
    hedging: bool = False


@dataclass(slots=True)
class StrategyParams:
    min_exec_adx: int = 16
    min_exec_atr_ratio: float = 0.90
    min_ema_distance_atr: float = 0.05
    pullback_overshoot_atr: float = 0.70
    cooldown_bars: int = 3
    direction_cooldown_bars: int = 2
    long_rsi_min: int = 53
    short_rsi_max: int = 47
    stop_atr_mult: float = 1.5
    tp1_rr: float = 1.0
    tp2_rr: float = 2.4
    trail_atr_mult: float = 2.25
    add_on_profit_atr: float = 0.8
    use_broker_executable_long_tp1: bool = False
    long_tp1_leg_fraction: float = 0.5
    long_tp1_profit_lock_atr: float = 0.0
    long_tp2_profit_lock_rr: float = 0.0
    long_tp2_trail_atr_mult: float = 0.0
    use_long_distance_cap: bool = False
    max_long_distance_atr: float = 2.0
    use_short_distance_cap: bool = True
    max_short_distance_atr: float = 1.6
    use_short_ema20_proximity_filter: bool = True
    max_short_ema20_gap_atr: float = 0.9
    use_short_squeeze_filter: bool = True
    short_squeeze_rsi_threshold: float = 48.0
    short_squeeze_rsi_rebound_delta: float = 2.0
    short_squeeze_require_falling_adx: bool = True

    weekly_fast_length: int = 50
    weekly_slow_length: int = 200
    daily_fast_length: int = 20
    daily_mid_length: int = 50
    daily_slow_length: int = 200
    daily_slope_lookback: int = 5
    daily_di_length: int = 14
    daily_adx_smoothing: int = 14
    min_daily_adx: float = 18.0
    daily_atr_length: int = 14
    daily_atr_ma_length: int = 20
    min_daily_atr_ratio: float = 0.95
    use_daily_adx_filter: bool = False
    use_daily_atr_expansion: bool = False

    exec_fast_length: int = 20
    exec_mid_length: int = 50
    exec_slow_length: int = 200
    exec_slope_lookback: int = 5
    exec_di_length: int = 14
    exec_adx_smoothing: int = 14
    exec_atr_length: int = 14
    exec_atr_ma_length: int = 20
    rsi_length: int = 14
    continuation_lookback: int = 10
    add_on_gap_bars: int = 3
    breakeven_offset_atr: float = 0.05
    require_strong_resumption: bool = False


PARAMETER_GRID: dict[str, list[float | int]] = {
    "min_exec_adx": [16, 17, 18],
    "min_exec_atr_ratio": [0.85, 0.90, 0.95],
    "min_ema_distance_atr": [0.05, 0.10],
    "pullback_overshoot_atr": [0.6, 0.7, 0.8],
    "cooldown_bars": [3, 4, 5],
    "direction_cooldown_bars": [2, 3, 4],
    "long_rsi_min": [52, 53, 54],
    "short_rsi_max": [46, 47, 48],
    "stop_atr_mult": [1.4, 1.5, 1.6],
    "tp2_rr": [2.2, 2.4, 2.6],
    "trail_atr_mult": [2.0, 2.25, 2.5],
    "add_on_profit_atr": [0.7, 0.8, 0.9],
}


PHASES: dict[str, list[str]] = {
    "phase1_entry_frequency": [
        "min_exec_adx",
        "min_exec_atr_ratio",
        "min_ema_distance_atr",
        "pullback_overshoot_atr",
        "cooldown_bars",
        "direction_cooldown_bars",
    ],
    "phase2_directional_quality": [
        "long_rsi_min",
        "short_rsi_max",
    ],
    "phase3_trade_management": [
        "stop_atr_mult",
        "tp2_rr",
        "trail_atr_mult",
        "add_on_profit_atr",
    ],
}


@dataclass(slots=True)
class Paths:
    root: Path = Path.cwd()
    data_dir: Path = field(init=False)
    output_dir: Path = field(init=False)
    studies_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.data_dir = self.root / "data"
        self.output_dir = self.root / "research_output"
        self.studies_dir = self.output_dir / "studies"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.studies_dir.mkdir(parents=True, exist_ok=True)
