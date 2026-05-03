from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from src.strategy import generate_signal as generate_baseline_signal


ALLOWED_STRATEGY_VARIANTS = {"baseline", "4h_d2", "4h_d6"}
FOUR_HOUR_DRY_RUN_VARIANTS = {"4h_d2", "4h_d6"}


def normalize_strategy_variant(value: Optional[str]) -> str:
    if value is None or value.strip() == "":
        return "baseline"
    return value.strip().lower()


def validate_runtime_strategy_settings(
    *,
    strategy_variant: str,
    timeframe: str,
    dry_run: bool,
    atr_percentile_window: int,
    ema200_slope_lookback: int,
) -> None:
    variant = normalize_strategy_variant(strategy_variant)
    if variant not in ALLOWED_STRATEGY_VARIANTS:
        allowed = ", ".join(sorted(ALLOWED_STRATEGY_VARIANTS))
        raise ValueError(
            f"Unknown STRATEGY_VARIANT={strategy_variant!r}. Allowed values: {allowed}."
        )
    if atr_percentile_window < 1:
        raise ValueError("ATR_PERCENTILE_WINDOW must be at least 1")
    if ema200_slope_lookback < 1:
        raise ValueError("EMA200_SLOPE_LOOKBACK must be at least 1")
    if variant not in FOUR_HOUR_DRY_RUN_VARIANTS:
        return
    if not dry_run:
        raise ValueError(
            f"STRATEGY_VARIANT={variant} is research/dry-run-only. Set DRY_RUN=1."
        )
    if timeframe != "4h":
        raise ValueError(
            f"STRATEGY_VARIANT={variant} requires TIMEFRAME=4h. "
            "This prevents accidentally running a 4h research candidate on another timeframe."
        )


def generate_strategy_signal(
    df: pd.DataFrame,
    *,
    strategy_variant: str,
    timeframe: str,
    atr_percentile_window: int = 200,
    ema200_slope_lookback: int = 12,
) -> dict[str, Any]:
    variant = normalize_strategy_variant(strategy_variant)
    if variant == "baseline":
        signal = generate_baseline_signal(df)
        return {
            **signal,
            "strategy_variant": "baseline",
            "raw_signal": signal.get("signal"),
            "raw_reason": signal.get("reason"),
        }

    validate_runtime_strategy_settings(
        strategy_variant=variant,
        timeframe=timeframe,
        dry_run=True,
        atr_percentile_window=atr_percentile_window,
        ema200_slope_lookback=ema200_slope_lookback,
    )

    if variant == "4h_d2":
        return _generate_4h_variant_d_signal(
            df,
            strategy_variant=variant,
            atr_percentile_threshold=0.60,
            atr_percentile_window=atr_percentile_window,
            ema200_slope_lookback=ema200_slope_lookback,
            require_ema200_slope=False,
        )
    if variant == "4h_d6":
        return _generate_4h_variant_d_signal(
            df,
            strategy_variant=variant,
            atr_percentile_threshold=0.70,
            atr_percentile_window=atr_percentile_window,
            ema200_slope_lookback=ema200_slope_lookback,
            require_ema200_slope=True,
        )

    allowed = ", ".join(sorted(ALLOWED_STRATEGY_VARIANTS))
    raise ValueError(f"Unknown STRATEGY_VARIANT={strategy_variant!r}. Allowed values: {allowed}.")


def _generate_4h_variant_d_signal(
    df: pd.DataFrame,
    *,
    strategy_variant: str,
    atr_percentile_threshold: float,
    atr_percentile_window: int,
    ema200_slope_lookback: int,
    require_ema200_slope: bool,
) -> dict[str, Any]:
    if df.empty:
        return {
            "signal": "hold",
            "reason": "no_data",
            "strategy_variant": strategy_variant,
            "raw_signal": "hold",
            "raw_reason": "no_data",
        }

    latest = df.iloc[-1]
    payload = _latest_payload(latest)
    payload.update(
        {
            "strategy_variant": strategy_variant,
            "atr_percentile": _rolling_percentile(
                df["atr14"], window=atr_percentile_window
            ),
            "ema200_slope_ok": _ema200_slope_ok(
                df, lookback=ema200_slope_lookback
            ),
        }
    )

    required = ["close", "ema20", "ema60", "ema200", "rsi14", "atr14"]
    if latest[required].isna().any():
        return {
            **payload,
            "signal": "hold",
            "raw_signal": "hold",
            "raw_reason": "indicators_not_ready",
            "reason": "indicators_not_ready",
        }

    close = float(latest["close"])
    ema20 = float(latest["ema20"])
    ema60 = float(latest["ema60"])
    ema200 = float(latest["ema200"])
    rsi14 = float(latest["rsi14"])

    confirmed_exit = _confirmed_close_below_ema20(df)
    baseline_entry = close > ema200 and ema20 > ema60 and 45 <= rsi14 <= 70
    raw_signal = "exit" if confirmed_exit else "long_entry" if baseline_entry else "hold"
    raw_reason = (
        "confirmed_close_below_ema20"
        if confirmed_exit
        else "trend_alignment_rsi_filter"
        if baseline_entry
        else "conditions_not_met"
    )

    if confirmed_exit:
        return {
            **payload,
            "signal": "exit",
            "raw_signal": raw_signal,
            "raw_reason": raw_reason,
            "reason": "confirmed_close_below_ema20",
        }

    if not baseline_entry:
        return {
            **payload,
            "signal": "hold",
            "raw_signal": raw_signal,
            "raw_reason": raw_reason,
            "reason": "conditions_not_met",
        }

    atr_percentile = payload["atr_percentile"]
    if atr_percentile is None:
        return {
            **payload,
            "signal": "hold",
            "raw_signal": raw_signal,
            "raw_reason": raw_reason,
            "reason": "atr_percentile_not_ready",
        }
    if float(atr_percentile) >= atr_percentile_threshold:
        return {
            **payload,
            "signal": "hold",
            "raw_signal": raw_signal,
            "raw_reason": raw_reason,
            "reason": f"atr_percentile_gte_{int(atr_percentile_threshold * 100)}",
        }

    ema200_slope_ok = payload["ema200_slope_ok"]
    if require_ema200_slope and ema200_slope_ok is None:
        return {
            **payload,
            "signal": "hold",
            "raw_signal": raw_signal,
            "raw_reason": raw_reason,
            "reason": "ema200_slope_not_ready",
        }
    if require_ema200_slope and not bool(ema200_slope_ok):
        return {
            **payload,
            "signal": "hold",
            "raw_signal": raw_signal,
            "raw_reason": raw_reason,
            "reason": "ema200_slope_filter",
        }

    return {
        **payload,
        "signal": "long_entry",
        "raw_signal": raw_signal,
        "raw_reason": raw_reason,
        "reason": f"{strategy_variant}_entry_filters",
    }


def _latest_payload(latest: pd.Series) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if "timestamp" in latest:
        payload["timestamp"] = latest["timestamp"]
    for column in ("close", "ema20", "ema60", "ema200", "rsi14", "atr14"):
        if column in latest and pd.notna(latest[column]):
            payload[column] = float(latest[column])
    return payload


def _rolling_percentile(series: pd.Series, *, window: int) -> Optional[float]:
    valid_values = series.dropna()
    if len(valid_values) < window:
        return None
    window_values = valid_values.iloc[-window:]
    current = float(window_values.iloc[-1])
    return float((window_values <= current).sum() / len(window_values))


def _ema200_slope_ok(df: pd.DataFrame, *, lookback: int) -> Optional[bool]:
    if len(df) <= lookback:
        return None
    current = df.iloc[-1]["ema200"]
    previous = df.iloc[-1 - lookback]["ema200"]
    if pd.isna(current) or pd.isna(previous):
        return None
    return bool(float(current) > float(previous))


def _confirmed_close_below_ema20(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    return _close_below_ema20(latest) and _close_below_ema20(previous)


def _close_below_ema20(row: pd.Series) -> bool:
    if pd.isna(row["close"]) or pd.isna(row["ema20"]):
        return False
    return bool(float(row["close"]) < float(row["ema20"]))
