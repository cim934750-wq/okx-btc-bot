from __future__ import annotations

import math
from typing import Any

import pandas as pd

from btc_signal.config import BtcSignalConfig
from btc_signal.features import (
    EVIDENCE_FIELDS,
    LONG1_CONDITION_COLUMNS,
    build_long1_feature_frame,
    load_btc_4h_csv,
    missing_feature_columns,
)
from btc_signal.models import SignalAction, SignalDecision
from research.config import StrategyParams


def _json_scalar(value: Any) -> Any:
    if isinstance(value, (bool, str)) or value is None:
        return value
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return float(value)
    return value


def _evidence_from_row(row: pd.Series) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for field in EVIDENCE_FIELDS:
        value = row[field]
        if field in LONG1_CONDITION_COLUMNS:
            evidence[field] = bool(value)
        else:
            evidence[field] = _json_scalar(value)
    return evidence


def _confidence_label(passed_count: int, total_count: int, has_signal: bool) -> str:
    if has_signal:
        return "strong"
    if passed_count == 0:
        return "none"
    if passed_count >= max(total_count - 2, 1):
        return "candidate"
    return "weak"


def _blocked_decision(
    config: BtcSignalConfig,
    reason: str,
    missing_conditions: list[str] | None = None,
    timestamp: str | None = None,
) -> SignalDecision:
    return SignalDecision(
        timestamp=timestamp,
        symbol=config.symbol,
        timeframe=config.timeframe,
        decision=SignalAction.BLOCKED.value,
        signal_name=None,
        evidence={},
        missing_conditions=missing_conditions or [],
        passed_conditions=[],
        confidence_label="none",
        reasoning_summary=reason,
    )


def evaluate_feature_frame(feature_frame: pd.DataFrame, config: BtcSignalConfig) -> SignalDecision:
    if feature_frame.empty:
        return _blocked_decision(config, "Feature frame is empty after indicator preparation.")

    missing_columns = missing_feature_columns(feature_frame)
    if missing_columns:
        return _blocked_decision(
            config,
            f"Feature frame is missing required columns: {', '.join(missing_columns)}.",
            missing_columns,
        )

    frame = feature_frame.sort_index()
    latest = frame.iloc[-1]
    timestamp = frame.index[-1].isoformat()

    required_values = [*EVIDENCE_FIELDS, "starter_long_signal"]
    nan_fields = [field for field in required_values if pd.isna(latest[field])]
    if nan_fields:
        return _blocked_decision(
            config,
            f"Latest feature row contains NaN values: {', '.join(nan_fields)}.",
            nan_fields,
            timestamp,
        )

    passed_conditions = [condition for condition in LONG1_CONDITION_COLUMNS if bool(latest[condition])]
    missing_conditions = [condition for condition in LONG1_CONDITION_COLUMNS if not bool(latest[condition])]
    has_signal = bool(latest["starter_long_signal"])
    decision = SignalAction.LONG_SIGNAL.value if has_signal else (
        SignalAction.WATCH.value if len(passed_conditions) >= len(LONG1_CONDITION_COLUMNS) - 2 else SignalAction.WAIT.value
    )
    signal_name = "Long1" if has_signal else None
    confidence_label = _confidence_label(len(passed_conditions), len(LONG1_CONDITION_COLUMNS), has_signal)
    evidence = _evidence_from_row(latest)

    if has_signal:
        summary = "Long1 candidate is active because all required Long1 conditions passed on the latest completed 4h candle."
    elif decision == SignalAction.WATCH.value:
        summary = (
            "No Long1 signal: most regime and execution conditions passed, "
            f"but missing conditions are {', '.join(missing_conditions)}."
        )
    else:
        summary = (
            "No Long1 signal: required Long1 conditions are incomplete. "
            f"Passed {len(passed_conditions)}/{len(LONG1_CONDITION_COLUMNS)} conditions."
        )

    return SignalDecision(
        timestamp=timestamp,
        symbol=config.symbol,
        timeframe=config.timeframe,
        decision=decision,
        signal_name=signal_name,
        evidence=evidence,
        missing_conditions=missing_conditions,
        passed_conditions=passed_conditions,
        confidence_label=confidence_label,
        reasoning_summary=summary,
    )


def generate_signal_from_ohlcv(
    df_4h: pd.DataFrame,
    config: BtcSignalConfig,
    params: StrategyParams | None = None,
) -> tuple[SignalDecision, pd.DataFrame]:
    feature_frame = build_long1_feature_frame(df_4h, params or StrategyParams())
    return evaluate_feature_frame(feature_frame, config), feature_frame


def generate_signal(config: BtcSignalConfig, params: StrategyParams | None = None) -> tuple[SignalDecision, pd.DataFrame]:
    df_4h = load_btc_4h_csv(str(config.data_path))
    return generate_signal_from_ohlcv(df_4h, config, params or StrategyParams())
