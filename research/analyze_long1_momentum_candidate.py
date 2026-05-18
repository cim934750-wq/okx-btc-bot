from __future__ import annotations

import argparse

import pandas as pd

from research.config import Paths
from research.data import load_ohlcv_csv
from research.indicators import build_feature_frame
from research.long_only_candidate import long_only_backtest_config, long_only_production_params
from research.strategy import run_backtest


PROFILE_SPECS: dict[str, dict[str, float | int]] = {
    "tight": {
        "reclaim_lookback_bars": 1,
        "close_gap_min": 0.30,
        "close_gap_max": 0.80,
        "exec_distance_min": 1.10,
        "exec_distance_max": 2.00,
        "cont_gap_cutoff": 0.05,
        "adx_min": 22.0,
        "di_spread_min": 7.0,
        "atr_ratio_min": 1.00,
    },
    "center": {
        "reclaim_lookback_bars": 2,
        "close_gap_min": 0.25,
        "close_gap_max": 0.90,
        "exec_distance_min": 1.00,
        "exec_distance_max": 2.25,
        "cont_gap_cutoff": 0.10,
        "adx_min": 20.0,
        "di_spread_min": 5.0,
        "atr_ratio_min": 0.95,
    },
    "loose": {
        "reclaim_lookback_bars": 2,
        "close_gap_min": 0.20,
        "close_gap_max": 1.00,
        "exec_distance_min": 0.90,
        "exec_distance_max": 2.50,
        "cont_gap_cutoff": 0.15,
        "adx_min": 18.0,
        "di_spread_min": 3.0,
        "atr_ratio_min": 0.90,
    },
}

PROFILE_ORDER = ["tight", "center", "loose"]
PROFILE_LABELS = [
    "momentum_persistence_candidate",
    "excluded_reclaim_damage",
    "excluded_breakout_like",
    "excluded_weakening_state",
    "excluded_depth_or_extension",
    "excluded_energy_quality",
    "other",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a profile-based momentum-persistence validation study on baseline Long1 trades."
    )
    parser.add_argument("--csv", required=True)
    parser.add_argument("--prefix", default="long1_momentum_candidate_profiles_round1")
    return parser.parse_args()


def _recent_close_below_ema20(frame: pd.DataFrame, entry_bar: int, lookback_bars: int) -> bool:
    start_bar = max(0, entry_bar - lookback_bars)
    prev_window = frame.iloc[start_bar:entry_bar].copy()
    if prev_window.empty:
        return False
    return bool((prev_window["close"] <= prev_window["ema20"]).any())


def _safe_float(value: object, fallback: float = 0.0) -> float:
    return float(value) if pd.notna(value) else fallback


def label_trade(frame: pd.DataFrame, trade: pd.Series) -> dict:
    entry_bar = int(trade["EntryBar"])
    entry_row = frame.iloc[entry_bar]

    entry_close = float(entry_row["close"])
    entry_ema20 = float(entry_row["ema20"])
    entry_cont_high = _safe_float(entry_row["cont_high"], float(entry_row["high"]))
    entry_atr = float(entry_row["atr"])
    entry_cont_gap_atr = max(entry_cont_high - entry_close, 0.0) / entry_atr if entry_atr > 0 else 0.0
    close_ema20_gap_atr = _safe_float(entry_row.get("close_ema20_gap_atr", 0.0))
    exec_distance_atr = float(entry_row["exec_distance_atr"])
    atr_ratio = float(entry_row["atr_ratio"])
    adx = float(entry_row["adx"])
    di_spread = float(entry_row["di_spread"])
    regime_label = str(entry_row["regime_label"])
    weekly_bull = bool(entry_row["weekly_bull"])
    daily_bull = bool(entry_row["daily_bull"])
    exec_bull_structure = bool(entry_row["exec_bull_structure"])
    exec_slope_up = bool(entry_row["exec_slope_up"])
    bull_alignment = weekly_bull and daily_bull and exec_bull_structure and exec_slope_up
    recent_close_below_ema20_1 = _recent_close_below_ema20(frame, entry_bar, 1)
    recent_close_below_ema20_2 = _recent_close_below_ema20(frame, entry_bar, 2)

    out: dict[str, object] = {
        "EntryTime": pd.to_datetime(trade["EntryTime"], utc=True),
        "ExitTime": pd.to_datetime(trade["ExitTime"], utc=True),
        "Tag": trade["Tag"],
        "PnL": float(trade["PnL"]),
        "ReturnPct": float(trade["ReturnPct"]),
        "entry_bar": entry_bar,
        "regime_label": regime_label,
        "bull_alignment": bull_alignment,
        "weekly_bull": weekly_bull,
        "daily_bull": daily_bull,
        "exec_bull_structure": exec_bull_structure,
        "exec_slope_up": exec_slope_up,
        "entry_close": entry_close,
        "entry_ema20": entry_ema20,
        "entry_cont_high": entry_cont_high,
        "entry_cont_gap_atr": entry_cont_gap_atr,
        "entry_close_ema20_gap_atr": close_ema20_gap_atr,
        "entry_exec_distance_atr": exec_distance_atr,
        "entry_atr_ratio": atr_ratio,
        "entry_adx": adx,
        "entry_di_spread": di_spread,
        "recent_close_below_ema20_1": recent_close_below_ema20_1,
        "recent_close_below_ema20_2": recent_close_below_ema20_2,
    }

    for profile_name in PROFILE_ORDER:
        spec = PROFILE_SPECS[profile_name]
        recent_close_below = bool(out[f"recent_close_below_ema20_{int(spec['reclaim_lookback_bars'])}"])
        breakout_like = (entry_close >= entry_cont_high) or (entry_cont_gap_atr <= float(spec["cont_gap_cutoff"]))
        depth_or_extension_fail = not (
            float(spec["close_gap_min"]) <= close_ema20_gap_atr <= float(spec["close_gap_max"])
            and float(spec["exec_distance_min"]) <= exec_distance_atr <= float(spec["exec_distance_max"])
        )
        energy_quality_fail = not (
            adx > float(spec["adx_min"])
            and di_spread > float(spec["di_spread_min"])
            and atr_ratio >= float(spec["atr_ratio_min"])
        )
        fixed_identity_fail = (not bull_alignment) or (regime_label == "weakening_trend") or (entry_close < entry_ema20)

        if regime_label == "weakening_trend":
            label = "excluded_weakening_state"
        elif recent_close_below:
            label = "excluded_reclaim_damage"
        elif breakout_like:
            label = "excluded_breakout_like"
        elif depth_or_extension_fail:
            label = "excluded_depth_or_extension"
        elif energy_quality_fail:
            label = "excluded_energy_quality"
        elif fixed_identity_fail:
            label = "other"
        else:
            label = "momentum_persistence_candidate"

        out[f"label_{profile_name}"] = label
        out[f"candidate_in_{profile_name}"] = label == "momentum_persistence_candidate"
        out[f"recent_close_below_ema20_{profile_name}"] = recent_close_below
        out[f"breakout_like_{profile_name}"] = breakout_like

    out["candidate_consensus_count"] = int(sum(bool(out[f"candidate_in_{name}"]) for name in PROFILE_ORDER))
    return out


def summarize_groups(df: pd.DataFrame, group_col: str, profile: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group_name in [
        "momentum_persistence_candidate",
        "remaining_baseline_long1",
        "excluded_reclaim_damage",
        "excluded_breakout_like",
        "excluded_weakening_state",
    ]:
        if group_name == "remaining_baseline_long1":
            sub = df[df[group_col] != "momentum_persistence_candidate"].copy()
        else:
            sub = df[df[group_col] == group_name].copy()
        count = int(len(sub))
        losers = int((sub["PnL"] <= 0).sum())
        winners = int((sub["PnL"] > 0).sum())
        loser_share = losers / count if count > 0 else 0.0
        avg_pnl = float(sub["PnL"].mean()) if count > 0 else 0.0
        rows.append(
            {
                "profile": profile,
                "group": group_name,
                "count": count,
                "losers": losers,
                "winners": winners,
                "loser_share": loser_share,
                "avg_pnl": avg_pnl,
            }
        )
    return pd.DataFrame(rows)


def summarize_exclusions(df: pd.DataFrame, group_col: str, profile: str) -> pd.DataFrame:
    sub = df[df[group_col].isin(PROFILE_LABELS)].copy()
    grouped = []
    for label in PROFILE_LABELS:
        label_sub = sub[sub[group_col] == label].copy()
        count = int(len(label_sub))
        losers = int((label_sub["PnL"] <= 0).sum())
        winners = int((label_sub["PnL"] > 0).sum())
        loser_share = losers / count if count > 0 else 0.0
        avg_pnl = float(label_sub["PnL"].mean()) if count > 0 else 0.0
        grouped.append(
            {
                "profile": profile,
                "label": label,
                "count": count,
                "losers": losers,
                "winners": winners,
                "loser_share": loser_share,
                "avg_pnl": avg_pnl,
            }
        )
    return pd.DataFrame(grouped)


def summarize_stability(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    stability_groups = [
        ("candidate_consensus_3_of_3", df[df["candidate_consensus_count"] == 3].copy()),
        ("candidate_consensus_2_of_3", df[df["candidate_consensus_count"] == 2].copy()),
        ("candidate_consensus_1_of_3", df[df["candidate_consensus_count"] == 1].copy()),
        ("candidate_consensus_0_of_3", df[df["candidate_consensus_count"] == 0].copy()),
    ]
    for bucket, sub in stability_groups:
        count = int(len(sub))
        losers = int((sub["PnL"] <= 0).sum())
        winners = int((sub["PnL"] > 0).sum())
        loser_share = losers / count if count > 0 else 0.0
        avg_pnl = float(sub["PnL"].mean()) if count > 0 else 0.0
        rows.append(
            {
                "stability_bucket": bucket,
                "count": count,
                "losers": losers,
                "winners": winners,
                "loser_share": loser_share,
                "avg_pnl": avg_pnl,
            }
        )
    return pd.DataFrame(rows)


def metric_lookup(summary: pd.DataFrame, profile: str, group: str, metric: str, default: float = 0.0) -> float:
    row = summary[(summary["profile"] == profile) & (summary["group"] == group)]
    if row.empty:
        return default
    return float(row.iloc[0][metric])


def stability_metric(summary: pd.DataFrame, bucket: str, metric: str, default: float = 0.0) -> float:
    row = summary[summary["stability_bucket"] == bucket]
    if row.empty:
        return default
    return float(row.iloc[0][metric])


def build_recommendation(
    labeled: pd.DataFrame,
    profile_summary: pd.DataFrame,
    stability_summary: pd.DataFrame,
) -> pd.DataFrame:
    all_long1_count = int(len(labeled))
    center_candidate_count = int(metric_lookup(profile_summary, "center", "momentum_persistence_candidate", "count", 0.0))
    center_candidate_loser_share = metric_lookup(
        profile_summary, "center", "momentum_persistence_candidate", "loser_share", 1.0
    )
    center_candidate_avg_pnl = metric_lookup(profile_summary, "center", "momentum_persistence_candidate", "avg_pnl", 0.0)
    remaining_loser_share = metric_lookup(profile_summary, "center", "remaining_baseline_long1", "loser_share", 1.0)
    remaining_avg_pnl = metric_lookup(profile_summary, "center", "remaining_baseline_long1", "avg_pnl", 0.0)
    reclaim_loser_share = metric_lookup(profile_summary, "center", "excluded_reclaim_damage", "loser_share", 1.0)
    reclaim_avg_pnl = metric_lookup(profile_summary, "center", "excluded_reclaim_damage", "avg_pnl", 0.0)
    breakout_loser_share = metric_lookup(profile_summary, "center", "excluded_breakout_like", "loser_share", 1.0)
    breakout_avg_pnl = metric_lookup(profile_summary, "center", "excluded_breakout_like", "avg_pnl", 0.0)

    center_candidate_share = (center_candidate_count / all_long1_count) if all_long1_count > 0 else 0.0
    meaningful_share = center_candidate_count >= 12 and center_candidate_share >= 0.10
    healthier_than_remaining = (
        center_candidate_loser_share <= (remaining_loser_share - 0.10)
        and center_candidate_avg_pnl > remaining_avg_pnl
    )
    healthier_than_reclaim = (
        center_candidate_loser_share < reclaim_loser_share and center_candidate_avg_pnl > reclaim_avg_pnl
    )
    not_materially_worse_than_breakout = (
        center_candidate_loser_share <= breakout_loser_share
        or ((center_candidate_loser_share - breakout_loser_share) <= 0.10 and center_candidate_avg_pnl > breakout_avg_pnl)
    )

    center_mask = labeled["candidate_in_center"].astype(bool)
    center_count = int(center_mask.sum())
    center_survival_share = (
        float((labeled.loc[center_mask, "candidate_consensus_count"] >= 2).mean()) if center_count > 0 else 0.0
    )
    stable_23_count = int(len(labeled[labeled["candidate_consensus_count"] >= 2]))
    stable_23_loser_share = (
        int((labeled.loc[labeled["candidate_consensus_count"] >= 2, "PnL"] <= 0).sum()) / stable_23_count
        if stable_23_count > 0
        else 0.0
    )
    stable_23_avg_pnl = (
        float(labeled.loc[labeled["candidate_consensus_count"] >= 2, "PnL"].mean()) if stable_23_count > 0 else 0.0
    )
    stable_3_loser_share = stability_metric(stability_summary, "candidate_consensus_3_of_3", "loser_share", 1.0)
    stable_3_avg_pnl = stability_metric(stability_summary, "candidate_consensus_3_of_3", "avg_pnl", 0.0)
    stable_2_loser_share = stability_metric(stability_summary, "candidate_consensus_2_of_3", "loser_share", 1.0)
    stable_2_avg_pnl = stability_metric(stability_summary, "candidate_consensus_2_of_3", "avg_pnl", 0.0)
    stable_bucket_healthier_than_remaining = (
        (
            stability_metric(stability_summary, "candidate_consensus_3_of_3", "count", 0.0) > 0
            and stable_3_loser_share < remaining_loser_share
            and stable_3_avg_pnl > remaining_avg_pnl
        )
        or (
            stability_metric(stability_summary, "candidate_consensus_2_of_3", "count", 0.0) > 0
            and stable_2_loser_share < remaining_loser_share
            and stable_2_avg_pnl > remaining_avg_pnl
        )
    )
    stability_acceptable = center_survival_share >= 0.60 and stable_bucket_healthier_than_remaining

    success = (
        meaningful_share
        and healthier_than_remaining
        and healthier_than_reclaim
        and not_materially_worse_than_breakout
        and stability_acceptable
    )

    return pd.DataFrame(
        [
            {
                "recommendation": (
                    "open_redesign_implementation_round"
                    if success
                    else "keep_as_redesign_evidence_only"
                ),
                "all_long1_count": all_long1_count,
                "center_candidate_count": center_candidate_count,
                "center_candidate_share": center_candidate_share,
                "center_candidate_loser_share": center_candidate_loser_share,
                "center_candidate_avg_pnl": center_candidate_avg_pnl,
                "remaining_loser_share": remaining_loser_share,
                "remaining_avg_pnl": remaining_avg_pnl,
                "reclaim_loser_share": reclaim_loser_share,
                "reclaim_avg_pnl": reclaim_avg_pnl,
                "breakout_loser_share": breakout_loser_share,
                "breakout_avg_pnl": breakout_avg_pnl,
                "center_candidate_survival_share_consensus_ge_2": center_survival_share,
                "stable_23_count": stable_23_count,
                "stable_23_loser_share": stable_23_loser_share,
                "stable_23_avg_pnl": stable_23_avg_pnl,
                "meaningful_share_pass": meaningful_share,
                "healthier_than_remaining_pass": healthier_than_remaining,
                "healthier_than_reclaim_pass": healthier_than_reclaim,
                "not_materially_worse_than_breakout_pass": not_materially_worse_than_breakout,
                "stability_acceptable_pass": stability_acceptable,
            }
        ]
    )


def main() -> None:
    args = parse_args()
    paths = Paths()
    raw_df = load_ohlcv_csv(args.csv)
    params = long_only_production_params()
    bt_config = long_only_backtest_config()

    _, trades = run_backtest(raw_df, params, bt_config)
    long1_trades = trades[trades["Tag"] == "Long1"].copy()
    frame = build_feature_frame(raw_df, params)
    labeled = pd.DataFrame([label_trade(frame, trade) for _, trade in long1_trades.iterrows()])

    profile_summary = pd.concat(
        [summarize_groups(labeled, f"label_{profile}", profile) for profile in PROFILE_ORDER],
        ignore_index=True,
    )
    exclusion_summary = pd.concat(
        [summarize_exclusions(labeled, f"label_{profile}", profile) for profile in PROFILE_ORDER],
        ignore_index=True,
    )
    stability_summary = summarize_stability(labeled)
    recommendation_df = build_recommendation(labeled, profile_summary, stability_summary)

    prefix = paths.output_dir / args.prefix
    trade_labels_path = prefix.with_name(f"{prefix.name}.trade_labels_all.csv")
    profile_summary_path = prefix.with_name(f"{prefix.name}.profile_distribution_summary.csv")
    exclusion_summary_path = prefix.with_name(f"{prefix.name}.exclusion_reason_summary.csv")
    stability_summary_path = prefix.with_name(f"{prefix.name}.candidate_stability_summary.csv")
    recommendation_path = prefix.with_name(f"{prefix.name}.recommendation.csv")

    labeled.to_csv(trade_labels_path, index=False)
    profile_summary.to_csv(profile_summary_path, index=False)
    exclusion_summary.to_csv(exclusion_summary_path, index=False)
    stability_summary.to_csv(stability_summary_path, index=False)
    recommendation_df.to_csv(recommendation_path, index=False)

    print(f"Saved {trade_labels_path}")
    print(f"Saved {profile_summary_path}")
    print(f"Saved {exclusion_summary_path}")
    print(f"Saved {stability_summary_path}")
    print(f"Saved {recommendation_path}")
    print(profile_summary.to_string(index=False))
    print(stability_summary.to_string(index=False))
    print(recommendation_df.to_string(index=False))


if __name__ == "__main__":
    main()
