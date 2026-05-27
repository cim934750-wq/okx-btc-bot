from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from btc_signal.config import BtcSignalConfig
from btc_signal.features import make_synthetic_ohlcv
from btc_signal.models import to_jsonable, utc_now_iso
from btc_signal.paper_state import load_paper_state, record_paper_long, save_paper_state
from btc_signal.reporting import concise_json, write_decision_log
from btc_signal.response_engine import decide_response
from btc_signal.risk_engine import assess_risk
from btc_signal.signal_engine import generate_signal, generate_signal_from_ohlcv


def run_once(config: BtcSignalConfig | None = None, now: datetime | None = None) -> dict[str, Any]:
    cfg = config or BtcSignalConfig(root=Path.cwd())
    cfg.runtime_dir.mkdir(parents=True, exist_ok=True)
    cfg.log_dir.mkdir(parents=True, exist_ok=True)

    paper_state = load_paper_state(cfg.paper_state_path, symbol=cfg.symbol)
    data_source = str(cfg.data_path)
    used_synthetic_data = False

    if cfg.data_path.exists():
        signal, feature_frame = generate_signal(cfg)
    else:
        used_synthetic_data = True
        data_source = "synthetic_fixture_missing_csv"
        synthetic = make_synthetic_ohlcv(end=now or datetime.now(timezone.utc))
        signal, feature_frame = generate_signal_from_ohlcv(synthetic, cfg)

    risk = assess_risk(signal, feature_frame, cfg, paper_state=paper_state, now=now)
    response = decide_response(signal, risk, paper_state=paper_state)

    if response.action == "PAPER_LONG":
        paper_state = record_paper_long(paper_state, signal)
    save_paper_state(paper_state, cfg.paper_state_path)

    result: dict[str, Any] = {
        "run_at": utc_now_iso(),
        "mode": "paper_dry_run_only",
        "data_source": data_source,
        "used_synthetic_data": used_synthetic_data,
        "safety": {
            "api_keys_required": False,
            "live_orders_enabled": False,
            "live_trading_action": None,
        },
        "signal": signal,
        "risk": risk,
        "response": response,
        "paper_state": paper_state,
    }
    log_path = write_decision_log(result, cfg.log_dir)
    result["log_path"] = str(log_path)
    return to_jsonable(result)


def run_loop(interval_seconds: int | None = None, config: BtcSignalConfig | None = None) -> None:
    while True:
        print(concise_json(run_once(config=config)))
        if interval_seconds is None:
            return
        time.sleep(interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTC Long1 signal-response MVP in paper/dry-run mode.")
    parser.add_argument("--data-path", default=None, help="Optional BTCUSDT 4h CSV path.")
    parser.add_argument("--interval-seconds", type=int, default=None, help="Optional loop interval. Omit to run once.")
    return parser


def config_from_args(args: argparse.Namespace) -> BtcSignalConfig:
    cfg = BtcSignalConfig(root=Path.cwd())
    if args.data_path:
        cfg.data_path = Path(args.data_path)
    return cfg
