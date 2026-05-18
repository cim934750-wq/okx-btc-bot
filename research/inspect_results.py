from __future__ import annotations

import argparse
import json
from pathlib import Path

import optuna
import pandas as pd

from research.config import Paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Optuna study results.")
    parser.add_argument("--study-name", required=True)
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = Paths()
    csv_path = paths.output_dir / f"{args.study_name}.top_trials.csv"
    summary_path = paths.output_dir / f"{args.study_name}.summary.json"
    db_path = paths.studies_dir / f"{args.study_name}.db"

    if csv_path.exists() and (not db_path.exists() or db_path.stat().st_size == 0):
        df = pd.read_csv(csv_path).head(args.top)
        print(df.to_string(index=False))
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            print("\nSummary:")
            print(json.dumps(summary, indent=2))
        return

    storage = f"sqlite:///{db_path.as_posix()}"
    study = optuna.load_study(study_name=args.study_name, storage=storage)

    rows: list[dict] = []
    for trial in sorted(study.trials, key=lambda t: t.value if t.value is not None else -1e9, reverse=True)[: args.top]:
        row = {"trial_number": trial.number, "objective": trial.value}
        row.update(trial.user_attrs.get("params", {}))
        row.update(trial.user_attrs.get("metrics", {}))
        rows.append(row)

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
