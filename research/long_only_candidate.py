from __future__ import annotations

from dataclasses import replace

from research.config import BacktestConfig, StrategyParams


DATE_SPLITS = [
    ("full_sample", None, None),
    ("2019_2022", "2019-01-01", "2022-12-31 23:59:59"),
    ("2023_2024", "2023-01-01", "2024-12-31 23:59:59"),
    ("2025_2026", "2025-01-01", "2026-04-12 23:59:59"),
]


def long_only_backtest_config() -> BacktestConfig:
    return BacktestConfig(
        allow_longs=True,
        allow_shorts=False,
        enable_add_on_entries=True,
    )


def long_only_no_addons_backtest_config() -> BacktestConfig:
    return BacktestConfig(
        allow_longs=True,
        allow_shorts=False,
        enable_add_on_entries=False,
        add_on_size=0.0,
    )


def long_only_production_params() -> StrategyParams:
    return StrategyParams()


def long_only_production_params_with_fix() -> StrategyParams:
    return replace(
        StrategyParams(),
        use_broker_executable_long_tp1=True,
        long_tp1_leg_fraction=0.5,
    )


def long_only_split_leg_experiment_params(
    long_tp1_leg_fraction: float,
    tp1_rr: float,
    long_tp2_trail_atr_mult: float,
) -> StrategyParams:
    return replace(
        StrategyParams(),
        use_broker_executable_long_tp1=True,
        long_tp1_leg_fraction=long_tp1_leg_fraction,
        tp1_rr=tp1_rr,
        long_tp2_trail_atr_mult=long_tp2_trail_atr_mult,
    )
