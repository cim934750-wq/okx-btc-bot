from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path

import optuna
import pandas as pd

from research.config import BacktestConfig, PARAMETER_GRID, PHASES, Paths, StrategyParams
from research.data import load_ohlcv_csv
from research.strategy import extract_metrics, metrics_with_params, run_backtest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimize BTC MTF strategy with Optuna.")
    parser.add_argument("--csv", required=True, help="Path to 4H OHLCV CSV.")
    parser.add_argument("--phase", required=True, choices=list(PHASES.keys()))
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--study-name", default=None)
    return parser.parse_args()


def objective_factory(
    df: pd.DataFrame,
    phase: str,
    bt_config: BacktestConfig,
) -> callable:
    keys = PHASES[phase]

    def objective(trial: optuna.Trial) -> float:
        params = StrategyParams()
        for key in keys:
            values = PARAMETER_GRID[key]
            chosen = trial.suggest_categorical(key, values)
            params = replace(params, **{key: chosen})

        stats, trades = run_backtest(df, params, bt_config)
        metrics = extract_metrics(stats, trades)

        trial.set_user_attr("metrics", metrics)
        trial.set_user_attr("params", asdict(params))

        if metrics["total_trades"] < 35:
            return -1e9
        if metrics["profit_factor"] < 1.15:
            return -1e9
        if metrics["avg_trade"] <= 0:
            return -1e9
        if metrics["max_drawdown_pct"] > 25:
            return -1e9

        score = (
            metrics["expectancy"] * 3.0
            + metrics["net_profit"] / 1000.0
            + metrics["profit_factor"] * 20.0
            - metrics["max_drawdown_pct"] * 2.0
        )
        return score

    return objective


def main() -> None:
    args = parse_args()
    paths = Paths()
    df = load_ohlcv_csv(args.csv)
    bt_config = BacktestConfig()

    study_name = args.study_name or f"{args.phase}_btc4h"
    storage = f"sqlite:///{(paths.studies_dir / f'{study_name}.db').as_posix()}"
    sampler = optuna.samplers.GridSampler({key: PARAMETER_GRID[key] for key in PHASES[args.phase]})
    try:
        study = optuna.create_study(
            study_name=study_name,
            storage=storage,
            load_if_exists=True,
            direction="maximize",
            sampler=sampler,
        )
        storage_mode = "sqlite"
    except Exception:
        study = optuna.create_study(
            study_name=study_name,
            direction="maximize",
            sampler=sampler,
        )
        storage_mode = "memory"
    study.optimize(objective_factory(df, args.phase, bt_config), n_trials=args.trials)

    rows: list[dict] = []
    ranked_trials = sorted(
        [trial for trial in study.trials if trial.value is not None],
        key=lambda trial: trial.value,
        reverse=True,
    )
    for trial in ranked_trials[:20]:
        row = {}
        row.update(trial.user_attrs.get("params", {}))
        row.update(trial.user_attrs.get("metrics", {}))
        row["objective"] = trial.value
        row["trial_number"] = trial.number
        rows.append(row)

    out_path = paths.output_dir / f"{study_name}.top_trials.csv"
    pd.DataFrame(rows).sort_values("objective", ascending=False).to_csv(out_path, index=False)
    summary_path = paths.output_dir / f"{study_name}.summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "study_name": study_name,
                "storage_mode": storage_mode,
                "best_params": study.best_params,
                "best_value": study.best_value,
                "top_trials_csv": str(out_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved top trials to {out_path}")
    print(f"Saved study summary to {summary_path}")
    print("Best params:", study.best_params)
    print("Best value:", study.best_value)


if __name__ == "__main__":
    main()
