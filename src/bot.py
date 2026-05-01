from __future__ import annotations

import csv
import fcntl
import io
import json
import logging
import os
import signal as signal_module
import sys
import time
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.config import BotConfig, configure_logging, load_config
from src.data import fetch_ohlcv_dataframe
from src.exchange import OKXExchangeClient
from src.execution import OrderExecutor
from src.risk import RiskManager
from src.strategy import calculate_indicators, generate_signal


logger = logging.getLogger(__name__)
BOOT_ID = uuid.uuid4().hex


class ShutdownRequested(Exception):
    def __init__(self, signum: int):
        self.signum = signum
        super().__init__(f"signal_{signum}")


HEARTBEAT_COLUMNS = [
    "timestamp",
    "process_id",
    "boot_id",
    "loop_count",
    "symbol",
    "timeframe",
    "candle_timestamp",
    "close",
    "signal",
    "dry_run",
    "position_side",
    "equity_estimate",
    "realized_pnl",
    "unrealized_pnl",
    "error_count",
]

TRADES_COLUMNS = [
    "timestamp",
    "mode",
    "symbol",
    "side",
    "action",
    "price",
    "size",
    "reason",
    "realized_pnl",
    "dry_run",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_to_iso(value: Any) -> str:
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def default_paper_state(config: BotConfig) -> dict[str, Any]:
    now = utc_now_iso()
    today = datetime.now(timezone.utc).date().isoformat()
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return {
        "current_simulated_position": None,
        "entry_price": None,
        "size": 0.0,
        "stop_price": None,
        "realized_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "number_of_trades": 0,
        "last_signal": None,
        "last_update_timestamp": now,
        "LAST_PROCESSED_CANDLE_TIMESTAMP": None,
        "starting_equity": config.paper_starting_equity,
        "daily_start_date": today,
        "daily_start_equity": config.paper_starting_equity,
        "daily_entries_blocked": False,
        "monthly_start_month": month,
        "monthly_start_equity": config.paper_starting_equity,
        "monthly_entries_blocked": False,
        "last_error": None,
    }


def load_paper_state(config: BotConfig) -> dict[str, Any]:
    path = config.paper_state_path
    if not path.exists():
        return default_paper_state(config)
    try:
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (json.JSONDecodeError, OSError):
        logger.exception("Could not load paper state; starting with a fresh state")
        return default_paper_state(config)

    fresh = default_paper_state(config)
    fresh.update(state)
    return fresh


def fsync_directory(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        logger.debug("Could not open directory for fsync: %s", path, exc_info=True)
        return

    try:
        os.fsync(directory_fd)
    except OSError:
        logger.debug("Could not fsync directory: %s", path, exc_info=True)
    finally:
        os.close(directory_fd)


def save_paper_state(config: BotConfig, state: dict[str, Any]) -> None:
    state["last_update_timestamp"] = utc_now_iso()
    temp_path = config.paper_state_path.with_name(
        f".{config.paper_state_path.name}.{os.getpid()}.tmp"
    )

    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, config.paper_state_path)
        fsync_directory(config.paper_state_path.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def append_csv_text(path: Path, text: str) -> None:
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
    file_descriptor = os.open(path, flags, 0o644)
    try:
        data = text.encode("utf-8")
        while data:
            bytes_written = os.write(file_descriptor, data)
            if bytes_written == 0:
                raise OSError(f"Could not write to CSV log: {path}")
            data = data[bytes_written:]
        os.fsync(file_descriptor)
    finally:
        os.close(file_descriptor)


def render_csv_row(columns: list[str], row: Optional[dict[str, Any]] = None) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    if row is None:
        writer.writeheader()
    else:
        writer.writerow({column: row.get(column) for column in columns})
    return buffer.getvalue()


def csv_needs_header(path: Path) -> bool:
    try:
        return not path.exists() or path.stat().st_size == 0
    except OSError:
        logger.debug("Could not stat CSV path: %s", path, exc_info=True)
        return True


def csv_header_matches(path: Path, columns: list[str]) -> bool:
    if csv_needs_header(path):
        return True
    try:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            current_header = next(reader, [])
    except OSError:
        logger.debug("Could not read CSV header: %s", path, exc_info=True)
        return False
    return current_header == columns


def append_csv(path: Path, columns: list[str], row: dict[str, Any]) -> None:
    text = ""
    if csv_needs_header(path):
        text += render_csv_row(columns)
    text += render_csv_row(columns, row)
    append_csv_text(path, text)


def ensure_csv_logs(config: BotConfig) -> None:
    for path, columns in (
        (config.heartbeat_log_path, HEARTBEAT_COLUMNS),
        (config.trades_log_path, TRADES_COLUMNS),
    ):
        if not csv_header_matches(path, columns):
            archive_path = path.with_name(
                f"{path.name}.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.legacy"
            )
            logger.warning(
                "CSV schema changed; archiving %s to %s and creating a fresh header",
                path,
                archive_path,
            )
            path.replace(archive_path)
        if csv_needs_header(path):
            append_csv_text(path, render_csv_row(columns))


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def parse_lock_pid(lock_text: str) -> Optional[int]:
    for part in lock_text.replace("\n", " ").split():
        if not part.startswith("pid="):
            continue
        try:
            return int(part.split("=", 1)[1])
        except ValueError:
            return None
    return None


def acquire_runtime_lock(config: BotConfig):
    lock_path = config.runtime_dir / "bot.lock"
    lock_handle = lock_path.open("a+", encoding="utf-8")
    lock_handle.seek(0)
    existing_lock_text = lock_handle.read().strip()
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        existing_pid = parse_lock_pid(existing_lock_text)
        if existing_pid is not None:
            logger.error(
                "Runtime lock is held; lock_file=%s recorded_pid=%s pid_running=%s",
                lock_path,
                existing_pid,
                pid_is_running(existing_pid),
            )
        lock_handle.close()
        raise RuntimeError(
            f"Another bot process already holds the runtime lock: {lock_path}"
        ) from exc

    existing_pid = parse_lock_pid(existing_lock_text)
    if existing_lock_text and existing_pid is not None and not pid_is_running(existing_pid):
        logger.warning(
            "Replacing stale runtime lock metadata: lock_file=%s previous_pid=%s",
            lock_path,
            existing_pid,
        )

    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(
        f"pid={os.getpid()} boot_id={BOOT_ID} acquired_at={utc_now_iso()}\n"
    )
    lock_handle.flush()
    os.fsync(lock_handle.fileno())
    return lock_handle


def reserve_candle_decision(
    config: BotConfig, state: dict[str, Any], candle_timestamp: str
) -> None:
    state["LAST_PROCESSED_CANDLE_TIMESTAMP"] = candle_timestamp
    state["last_decision_reserved_timestamp"] = utc_now_iso()
    save_paper_state(config, state)
    logger.info("Reserved candle decision timestamp: %s", candle_timestamp)


def estimate_equity(state: dict[str, Any]) -> float:
    return (
        float(state.get("starting_equity") or 0.0)
        + float(state.get("realized_pnl") or 0.0)
        + float(state.get("unrealized_pnl") or 0.0)
    )


def update_unrealized_pnl(state: dict[str, Any], close: float) -> None:
    if state.get("current_simulated_position") == "long":
        entry = float(state.get("entry_price") or 0.0)
        size = float(state.get("size") or 0.0)
        state["unrealized_pnl"] = (close - entry) * size
    else:
        state["unrealized_pnl"] = 0.0


def private_account_snapshot(exchange_client: OKXExchangeClient) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    balance = exchange_client.fetch_balance()
    open_orders = exchange_client.fetch_open_orders()
    logger.info(
        "Private account snapshot: balance_available=%s open_orders=%s",
        bool(balance),
        len(open_orders),
    )
    return balance, open_orders


def write_heartbeat(
    config: BotConfig,
    state: dict[str, Any],
    signal: dict[str, Any],
    close: Optional[float],
    error_count: int,
    loop_count: int,
    candle_timestamp: Optional[str],
) -> None:
    append_csv(
        config.heartbeat_log_path,
        HEARTBEAT_COLUMNS,
        {
            "timestamp": utc_now_iso(),
            "process_id": os.getpid(),
            "boot_id": BOOT_ID,
            "loop_count": loop_count,
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "candle_timestamp": candle_timestamp,
            "close": close,
            "signal": signal.get("signal"),
            "dry_run": int(config.dry_run),
            "position_side": state.get("current_simulated_position"),
            "equity_estimate": estimate_equity(state),
            "realized_pnl": state.get("realized_pnl", 0.0),
            "unrealized_pnl": state.get("unrealized_pnl", 0.0),
            "error_count": error_count,
        },
    )
    logger.info(
        "Heartbeat: pid=%s boot_id=%s loop=%s symbol=%s timeframe=%s candle=%s close=%s signal=%s dry_run=%s position=%s equity=%.2f realized=%.2f unrealized=%.2f errors=%s",
        os.getpid(),
        BOOT_ID,
        loop_count,
        config.symbol,
        config.timeframe,
        candle_timestamp,
        close,
        signal.get("signal"),
        config.dry_run,
        state.get("current_simulated_position"),
        estimate_equity(state),
        float(state.get("realized_pnl") or 0.0),
        float(state.get("unrealized_pnl") or 0.0),
        error_count,
    )


def write_trade(
    config: BotConfig,
    *,
    side: str,
    action: str,
    price: float,
    size: float,
    reason: str,
    realized_pnl: float = 0.0,
) -> None:
    append_csv(
        config.trades_log_path,
        TRADES_COLUMNS,
        {
            "timestamp": utc_now_iso(),
            "mode": "paper" if config.dry_run else "live",
            "symbol": config.symbol,
            "side": side,
            "action": action,
            "price": price,
            "size": size,
            "reason": reason,
            "realized_pnl": realized_pnl,
            "dry_run": int(config.dry_run),
        },
    )


def simulate_paper_decision(
    config: BotConfig,
    risk_manager: RiskManager,
    state: dict[str, Any],
    signal: dict[str, Any],
    is_new_candle: bool,
) -> None:
    close = float(signal.get("close") or 0.0)
    atr = float(signal.get("atr14") or 0.0)
    update_unrealized_pnl(state, close)
    equity = estimate_equity(state)
    risk_manager.refresh_loss_windows(state, equity)

    if not is_new_candle:
        logger.info("No new candle; heartbeat only, no duplicate trade decision")
        return

    current_position = state.get("current_simulated_position")
    stop_price = state.get("stop_price")
    signal_name = signal.get("signal")

    if current_position == "long" and stop_price is not None and close <= float(stop_price):
        close_paper_position(config, state, close, "stop_loss")
        return

    if signal_name == "exit" and current_position == "long":
        close_paper_position(config, state, close, signal.get("reason", "exit_signal"))
        return

    if signal_name == "long_entry" and current_position is None:
        allowed, reason = risk_manager.can_enter_new_position(state, equity)
        if not allowed:
            logger.warning("Paper entry blocked: %s", reason)
            return
        size = risk_manager.position_size(equity=equity, entry_price=close, atr=atr)
        if size <= 0:
            logger.warning("Paper entry skipped: position size is zero")
            return
        fee_cost = close * size * config.fee_rate
        state["current_simulated_position"] = "long"
        state["entry_price"] = close
        state["size"] = size
        state["stop_price"] = risk_manager.stop_price_for_long(close, atr)
        state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) - fee_cost
        state["unrealized_pnl"] = 0.0
        state["number_of_trades"] = int(state.get("number_of_trades") or 0) + 1
        logger.info(
            "DRY_RUN=1 simulated long entry: price=%.2f size=%.10f stop=%.2f fee=%.4f",
            close,
            size,
            float(state["stop_price"]),
            fee_cost,
        )
        write_trade(
            config,
            side="buy",
            action="entry",
            price=close,
            size=size,
            reason=signal.get("reason", "long_entry"),
            realized_pnl=-fee_cost,
        )


def close_paper_position(
    config: BotConfig, state: dict[str, Any], price: float, reason: str
) -> None:
    entry = float(state.get("entry_price") or 0.0)
    size = float(state.get("size") or 0.0)
    gross_pnl = (price - entry) * size
    fee_cost = price * size * config.fee_rate
    net_pnl = gross_pnl - fee_cost
    state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) + net_pnl
    state["current_simulated_position"] = None
    state["entry_price"] = None
    state["size"] = 0.0
    state["stop_price"] = None
    state["unrealized_pnl"] = 0.0
    state["number_of_trades"] = int(state.get("number_of_trades") or 0) + 1
    logger.info(
        "DRY_RUN=1 simulated exit: price=%.2f size=%.10f net_pnl=%.4f reason=%s",
        price,
        size,
        net_pnl,
        reason,
    )
    write_trade(
        config,
        side="sell",
        action="exit",
        price=price,
        size=size,
        reason=reason,
        realized_pnl=net_pnl,
    )


def run_cycle(
    config: BotConfig,
    exchange_client: OKXExchangeClient,
    risk_manager: RiskManager,
    executor: OrderExecutor,
    state: dict[str, Any],
    loop_count: int,
    error_count: int = 0,
) -> None:
    df = fetch_ohlcv_dataframe(
        exchange_client,
        symbol=config.symbol,
        timeframe=config.timeframe,
        limit=config.candle_limit,
    )
    if df.empty:
        signal = {"signal": "hold", "reason": "no_candles"}
        write_heartbeat(config, state, signal, None, error_count, loop_count, None)
        save_paper_state(config, state)
        return

    df = calculate_indicators(df)
    signal = generate_signal(df)
    latest_close = float(df.iloc[-1]["close"])
    latest_candle_timestamp = timestamp_to_iso(df.iloc[-1]["timestamp"])

    update_unrealized_pnl(state, latest_close)
    equity = estimate_equity(state)
    risk_manager.refresh_loss_windows(state, equity)

    if config.api_keys_available:
        private_account_snapshot(exchange_client)

    last_processed = state.get("LAST_PROCESSED_CANDLE_TIMESTAMP")
    is_new_candle = (
        config.allow_repeat_candle_actions
        or last_processed is None
        or latest_candle_timestamp != last_processed
    )

    state["last_signal"] = signal.get("signal")

    if is_new_candle:
        reserve_candle_decision(config, state, latest_candle_timestamp)

    if config.dry_run:
        simulate_paper_decision(config, risk_manager, state, signal, is_new_candle)
    elif is_new_candle:
        handle_live_decision(config, risk_manager, executor, state, signal, equity)
    else:
        logger.info("No new candle; heartbeat only, no duplicate live trade decision")

    write_heartbeat(
        config,
        state,
        signal,
        latest_close,
        error_count,
        loop_count,
        latest_candle_timestamp,
    )
    save_paper_state(config, state)


def handle_live_decision(
    config: BotConfig,
    risk_manager: RiskManager,
    executor: OrderExecutor,
    state: dict[str, Any],
    signal: dict[str, Any],
    equity: float,
) -> None:
    signal_name = signal.get("signal")
    close = float(signal.get("close") or 0.0)
    atr = float(signal.get("atr14") or 0.0)
    current_position = state.get("current_simulated_position")
    stop_price = state.get("stop_price")

    if current_position == "long":
        should_exit = signal_name == "exit"
        exit_reason = signal.get("reason", "exit_signal")
        if stop_price is not None and close <= float(stop_price):
            should_exit = True
            exit_reason = "stop_loss"
        if not should_exit:
            logger.info("Live mode: position already tracked; no new entry")
            return

        size = float(state.get("size") or 0.0)
        result = executor.place_order(
            symbol=config.symbol,
            side="sell",
            action="exit",
            amount=size,
            price=None,
            state=state,
            equity=equity,
            reason=exit_reason,
        )
        logger.info("Live exit order result: %s", result)
        if result.get("status") not in {"blocked", "rejected"}:
            entry = float(state.get("entry_price") or close)
            realized_pnl = (close - entry) * size
            state["realized_pnl"] = float(state.get("realized_pnl") or 0.0) + realized_pnl
            state["current_simulated_position"] = None
            state["entry_price"] = None
            state["size"] = 0.0
            state["stop_price"] = None
            state["unrealized_pnl"] = 0.0
            write_trade(
                config,
                side="sell",
                action="exit",
                price=close,
                size=size,
                reason=exit_reason,
                realized_pnl=realized_pnl,
            )
        return

    if signal_name != "long_entry":
        logger.info("Live mode: no entry action for signal=%s", signal_name)
        return

    size = risk_manager.position_size(equity=equity, entry_price=close, atr=atr)
    result = executor.place_order(
        symbol=config.symbol,
        side="buy",
        action="entry",
        amount=size,
        price=None,
        state=state,
        equity=equity,
        reason=signal.get("reason", "long_entry"),
    )
    logger.info("Live order result: %s", result)
    if result.get("status") not in {"blocked", "rejected"}:
        state["current_simulated_position"] = "long"
        state["entry_price"] = close
        state["size"] = size
        state["stop_price"] = risk_manager.stop_price_for_long(close, atr)
        state["unrealized_pnl"] = 0.0
        state["number_of_trades"] = int(state.get("number_of_trades") or 0) + 1
        write_trade(
            config,
            side="buy",
            action="entry",
            price=close,
            size=size,
            reason=signal.get("reason", "long_entry"),
        )


def apply_pre_config_cli_env_overrides() -> None:
    if "--live-loop" in sys.argv:
        os.environ["BOT_MODE"] = "live_loop"
    if "--once" in sys.argv:
        os.environ["BOT_MODE"] = "once"
    if "--dry-run" in sys.argv:
        os.environ["DRY_RUN"] = "1"
    if "--okx-demo" in sys.argv:
        os.environ["OKX_DEMO"] = "1"


def apply_cli_overrides(config: BotConfig) -> BotConfig:
    updates: dict[str, Any] = {}
    if "--live-loop" in sys.argv:
        updates["bot_mode"] = "live_loop"
    if "--once" in sys.argv:
        updates["bot_mode"] = "once"
    if "--dry-run" in sys.argv:
        updates["dry_run"] = True
        updates["dry_run_raw"] = "1"
    if "--okx-demo" in sys.argv:
        updates["okx_demo"] = True
        updates["okx_demo_raw"] = "1"
    return replace(config, **updates) if updates else config


def install_shutdown_handlers() -> None:
    def _handle_shutdown(signum, _frame):
        raise ShutdownRequested(signum)

    signal_module.signal(signal_module.SIGTERM, _handle_shutdown)
    signal_module.signal(signal_module.SIGINT, _handle_shutdown)


def main() -> None:
    apply_pre_config_cli_env_overrides()
    config = apply_cli_overrides(load_config())
    configure_logging(config.log_level)
    install_shutdown_handlers()
    config.ensure_directories()
    runtime_lock = acquire_runtime_lock(config)
    ensure_csv_logs(config)

    logger.info(
        "Service starting: pid=%s boot_id=%s bot_mode=%s dry_run=%s okx_demo=%s symbol=%s timeframe=%s loop_interval_seconds=%s",
        os.getpid(),
        BOOT_ID,
        config.bot_mode,
        config.dry_run,
        config.okx_demo,
        config.symbol,
        config.timeframe,
        config.loop_interval_seconds,
    )
    logger.info("Runtime lock acquired: %s", runtime_lock.name)
    if config.dry_run:
        logger.info("DRY_RUN=1: real orders are disabled and will not be placed")
    if not config.api_keys_available:
        logger.warning(
            "API keys are missing; running market-data-only mode with private account checks disabled"
        )

    exchange_client = OKXExchangeClient(config)
    risk_manager = RiskManager(config)
    executor = OrderExecutor(config, exchange_client, risk_manager)
    state = load_paper_state(config)
    error_count = 0
    loop_count = 0
    exit_reason = "completed"

    try:
        if config.bot_mode == "once":
            loop_count = 1
            logger.info("BOT_MODE=once: running a single dry-run cycle")
            run_cycle(
                config,
                exchange_client,
                risk_manager,
                executor,
                state,
                loop_count,
                error_count,
            )
            return

        logger.info("BOT_MODE=%s: entering continuous loop", config.bot_mode)
        while True:
            loop_count += 1
            try:
                run_cycle(
                    config,
                    exchange_client,
                    risk_manager,
                    executor,
                    state,
                    loop_count,
                    error_count,
                )
                error_count = 0
            except ShutdownRequested as exc:
                exit_reason = str(exc)
                logger.info("Shutdown requested: %s", exit_reason)
                save_paper_state(config, state)
                return
            except Exception as exc:
                error_count += 1
                state["last_error"] = str(exc)
                logger.exception("Bot loop error; continuing after sleep")
                write_heartbeat(
                    config,
                    state,
                    {"signal": "error", "reason": exc.__class__.__name__},
                    None,
                    error_count,
                    loop_count,
                    None,
                )
                save_paper_state(config, state)
                if error_count >= config.error_threshold:
                    logger.error(
                        "Error threshold reached (%s); cooling down for %s seconds",
                        error_count,
                        config.cooldown_seconds,
                    )
                    time.sleep(config.cooldown_seconds)
                    error_count = 0
                else:
                    time.sleep(config.loop_interval_seconds)
                continue

            time.sleep(config.loop_interval_seconds)
    except ShutdownRequested as exc:
        exit_reason = str(exc)
        logger.info("Shutdown requested: %s", exit_reason)
        save_paper_state(config, state)
    finally:
        logger.info(
            "Service exiting: pid=%s boot_id=%s reason=%s loop_count=%s",
            os.getpid(),
            BOOT_ID,
            exit_reason,
            loop_count,
        )


if __name__ == "__main__":
    main()
