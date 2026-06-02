from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_btc_24h_paper_observation_cycle.py"


def _module():
    spec = importlib.util.spec_from_file_location("run_btc_24h_paper_observation_cycle", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_safe_command_plan_contains_only_existing_paper_commands() -> None:
    module = _module()
    plan = module.safe_command_plan("python")
    flattened = [" ".join(command) for command in plan]

    assert "python scripts/refresh_btcusdt_4h_data.py" in flattened
    assert "python scripts/run_btc_signal_once.py" in flattened
    assert "python scripts/report_btc_paper_status.py --format json" in flattened
    assert "python scripts/review_btc_order_intent_writer_design.py --format json" in flattened
    assert not any("order_intent" in item and "review" not in item and "audit" not in item for item in flattened)
    assert not any("adapter" in item for item in flattened)
    assert not any("live" in item for item in flattened)


def test_safety_boundary_disables_trading_paths() -> None:
    module = _module()
    safety = module.safety_boundary()

    assert safety["paper_observation_only"] is True
    assert safety["api_keys_required"] is False
    assert safety["private_api_calls"] is False
    assert safety["order_placement"] is False
    assert safety["order_intent_writer"] is False
    assert safety["runtime_order_intents"] is False
    assert safety["exchange_adapter"] is False
    assert safety["testnet_trading"] is False
    assert safety["live_trading"] is False


def test_cli_help_works() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--duration-hours" in result.stdout
    assert "--interval-minutes" in result.stdout
    assert "--dry-run" in result.stdout


def test_cli_dry_run_json_does_not_create_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "observation"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--once",
            "--format",
            "json",
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["dry_run"] is True
    assert payload["cycles_completed"] == 0
    assert payload["safety"]["order_placement"] is False
    assert payload["safety"]["live_trading"] is False
    assert not output_dir.exists()


def test_cli_dry_run_text_mentions_no_runtime_writes(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--output-dir",
            str(tmp_path / "observation"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Dry run: True" in result.stdout
    assert "no runtime files were written" in result.stdout
