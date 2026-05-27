from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from btc_signal.config import BtcSignalConfig
from btc_signal.features import RISK_FEATURE_COLUMNS, missing_feature_columns
from btc_signal.models import PaperState, RiskAssessment, RiskLevel, SignalDecision


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_finite_positive(value: Any) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0


def assess_risk(
    signal: SignalDecision,
    feature_frame: pd.DataFrame | None,
    config: BtcSignalConfig,
    paper_state: PaperState | None = None,
    now: datetime | None = None,
) -> RiskAssessment:
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    block_flags: list[str] = []
    high_flags: list[str] = []
    medium_flags: list[str] = []
    warnings: list[str] = []

    if signal.decision == "BLOCKED":
        block_flags.append("signal_blocked")
        warnings.append(signal.reasoning_summary)

    latest = None
    if feature_frame is None or feature_frame.empty:
        block_flags.append("missing_feature_frame")
    else:
        missing = missing_feature_columns(feature_frame, RISK_FEATURE_COLUMNS)
        if missing:
            block_flags.append("missing_feature_columns")
            warnings.append(f"Risk feature frame missing columns: {', '.join(missing)}.")
        else:
            frame = feature_frame.sort_index()
            latest = frame.iloc[-1]
            nan_fields = [field for field in RISK_FEATURE_COLUMNS if pd.isna(latest[field])]
            if nan_fields:
                block_flags.append("nan_latest_features")
                warnings.append(f"Latest risk features contain NaN: {', '.join(nan_fields)}.")

    signal_time = _parse_time(signal.timestamp)
    if signal_time is None:
        block_flags.append("missing_signal_timestamp")
    else:
        age_hours = (now_utc - signal_time).total_seconds() / 3600.0
        if age_hours > config.stale_after_hours:
            block_flags.append("stale_data")
            warnings.append(f"Latest candle is {age_hours:.2f} hours old; limit is {config.stale_after_hours:.2f} hours.")

    if latest is not None:
        atr = latest.get("atr")
        close = latest.get("close")
        atr_ratio = latest.get("atr_ratio")
        distance_atr = latest.get("exec_distance_atr")
        if not _is_finite_positive(atr):
            block_flags.append("invalid_atr")
            warnings.append("ATR is missing, zero, negative, or non-finite.")
        elif _is_finite_positive(close) and float(atr) / float(close) < config.min_atr_price_ratio:
            high_flags.append("atr_too_low")
            warnings.append("ATR is unusually low relative to price.")

        if _is_finite_positive(distance_atr) and float(distance_atr) > config.max_exec_distance_atr:
            high_flags.append("extreme_distance_from_ema50")
            warnings.append(
                f"Distance from EMA50 is {float(distance_atr):.2f} ATR; limit is {config.max_exec_distance_atr:.2f} ATR."
            )

        weekly_bull = bool(latest.get("weekly_bull"))
        daily_bull = bool(latest.get("daily_bull"))
        if weekly_bull != daily_bull:
            medium_flags.append("weekly_daily_regime_mismatch")
            warnings.append("Weekly and daily bull regime flags disagree.")

        if _is_finite_positive(atr_ratio) and float(atr_ratio) > config.sudden_volatility_atr_ratio:
            high_flags.append("sudden_volatility_expansion")
            warnings.append(
                f"ATR ratio is {float(atr_ratio):.2f}; limit is {config.sudden_volatility_atr_ratio:.2f}."
            )
        if feature_frame is not None and len(feature_frame) >= 2 and "atr_ratio" in feature_frame.columns:
            prev_atr_ratio = feature_frame.sort_index().iloc[-2]["atr_ratio"]
            if _is_finite_positive(prev_atr_ratio) and _is_finite_positive(atr_ratio):
                step_ratio = float(atr_ratio) / float(prev_atr_ratio)
                if step_ratio > config.sudden_volatility_step_ratio:
                    high_flags.append("sudden_volatility_step")
                    warnings.append(
                        f"ATR ratio expanded {step_ratio:.2f}x from the prior completed candle."
                    )

    if paper_state is not None:
        if paper_state.open_position:
            medium_flags.append("max_paper_position_already_open")
            warnings.append("Paper state already has an open position; duplicate paper entries are disabled.")
        if paper_state.last_signal_time and signal.decision == "LONG_SIGNAL":
            last_signal_time = _parse_time(paper_state.last_signal_time)
            if last_signal_time is not None:
                cooldown_hours = (now_utc - last_signal_time).total_seconds() / 3600.0
                if cooldown_hours < config.signal_cooldown_hours:
                    medium_flags.append("recent_signal_cooldown")
                    warnings.append(
                        f"Last paper signal was {cooldown_hours:.2f} hours ago; cooldown is {config.signal_cooldown_hours:.2f} hours."
                    )
        if abs(float(paper_state.max_drawdown_seen)) >= config.max_drawdown_allowed:
            block_flags.append("drawdown_guard")
            warnings.append(
                f"Paper drawdown guard triggered at {paper_state.max_drawdown_seen:.4f}; limit is {config.max_drawdown_allowed:.4f}."
            )

    all_flags = [*block_flags, *high_flags, *medium_flags]
    if block_flags:
        level = RiskLevel.BLOCK.value
        blocked_reason = "; ".join(warnings) if warnings else ", ".join(block_flags)
    elif high_flags:
        level = RiskLevel.HIGH.value
        blocked_reason = None
    elif medium_flags:
        level = RiskLevel.MEDIUM.value
        blocked_reason = None
    else:
        level = RiskLevel.LOW.value
        blocked_reason = None

    return RiskAssessment(
        risk_level=level,
        risk_flags=all_flags,
        blocked_reason=blocked_reason,
        warnings=warnings,
    )
