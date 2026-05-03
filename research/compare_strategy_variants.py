from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.strategy import calculate_indicators


HEARTBEAT_PATH = ROOT / "logs" / "heartbeat.csv"
TRADES_PATH = ROOT / "logs" / "trades.csv"
PAPER_STATE_PATH = ROOT / "data" / "paper_state.json"
REQUIRED_PRICE_COLUMNS = ["timestamp", "open", "high", "low", "close"]
OPTIONAL_COLUMNS = ["volume"]


@dataclass(frozen=True)
class Variant:
    name: str
    description: str


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    trade_return: float
    gross_pnl: float
    fee_cost: float
    pnl: float
    holding_candles: int
    exit_reason: str


@dataclass(frozen=True)
class SimulationConfig:
    starting_equity: float
    fee_rate: float
    slippage_rate_config: float
    max_risk_per_trade: float
    atr_stop_multiplier: float
    max_daily_loss: float
    max_monthly_loss: float


@dataclass
class Metrics:
    name: str
    total_return: float
    max_drawdown: float
    number_of_trades: int
    win_rate: float
    average_trade_return: float
    profit_factor: Optional[float]
    average_holding_time: float
    largest_loss: Optional[float]
    largest_win: Optional[float]
    whipsaw_count: int
    reduces_whipsaw: str = "n/a"
    reduces_overtrading: str = "n/a"


@dataclass
class SimulationResult:
    variant: Variant
    metrics: Metrics
    trades: list[Trade]
    equity_curve: list[float]


VARIANTS = [
    Variant("Baseline", "Entry: close > EMA200, EMA20 > EMA60, 45 <= RSI14 <= 70. Exit: close < EMA20."),
    Variant("Variant A", "Baseline entry plus EMA200 slope filter: EMA200 > EMA200 shifted by 12 candles."),
    Variant("Variant B", "Baseline entry plus anti-chase filter: (close - EMA20) / ATR14 <= 1.0."),
    Variant("Variant C", "Baseline rules plus 3-candle cooldown after each exit."),
    Variant("Variant D", "Baseline entry plus confirmed exit: two consecutive closes below EMA20."),
    Variant("Variant E", "Baseline entry plus ATR14 trailing stop, compared with baseline close < EMA20 exit."),
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row and any(value not in {None, ""} for value in row.values())
        ]


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw in {None, ""}:
        return default
    try:
        return float(str(raw))
    except ValueError:
        return default


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {
        column: str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    }
    df = df.rename(columns=renamed)
    aliases = {
        "date": "timestamp",
        "time": "timestamp",
        "datetime": "timestamp",
        "ts": "timestamp",
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume",
        "vol": "volume",
    }
    return df.rename(columns={source: target for source, target in aliases.items() if source in df.columns})


def load_ohlcv(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    df = normalize_columns(df)
    missing = [column for column in REQUIRED_PRICE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    result = df[REQUIRED_PRICE_COLUMNS + [column for column in OPTIONAL_COLUMNS if column in df.columns]].copy()
    numeric_columns = ["open", "high", "low", "close"]
    if "volume" in result.columns:
        numeric_columns.append("volume")
    result[numeric_columns] = result[numeric_columns].apply(pd.to_numeric, errors="coerce")

    timestamp = result["timestamp"]
    if pd.api.types.is_numeric_dtype(timestamp):
        unit = "ms" if float(timestamp.dropna().iloc[0]) > 10_000_000_000 else "s"
        result["timestamp"] = pd.to_datetime(timestamp, unit=unit, utc=True, errors="coerce")
    else:
        result["timestamp"] = pd.to_datetime(timestamp, utc=True, errors="coerce")

    result = result.dropna(subset=REQUIRED_PRICE_COLUMNS).sort_values("timestamp")
    result = result.drop_duplicates(subset=["timestamp"], keep="last").reset_index(drop=True)
    if result.empty:
        raise ValueError("no usable OHLC rows after parsing")
    return result


def candidate_data_paths(explicit_path: Optional[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in [explicit_path, os.getenv("OHLCV_PATH"), os.getenv("BACKTEST_DATA_PATH")]:
        if raw:
            paths.append(Path(raw).expanduser())

    preferred_names = [
        "BTCUSDT_1h.csv",
        "BTC_USDT_1h.csv",
        "BTC-USDT-1h.csv",
        "BTCUSDT_4h.csv",
        "BTC_USDT_4h.csv",
        "ohlcv.csv",
        "candles.csv",
    ]
    for folder in [ROOT / "data", ROOT / "research" / "data", ROOT]:
        for name in preferred_names:
            paths.append(folder / name)
        for pattern in ("*ohlcv*.csv", "*candle*.csv", "*BTC*USDT*.csv", "*ohlcv*.parquet", "*candle*.parquet", "*BTC*USDT*.parquet"):
            paths.extend(folder.glob(pattern))

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def find_ohlcv_data(explicit_path: Optional[str]) -> tuple[Optional[Path], Optional[pd.DataFrame], list[str]]:
    errors: list[str] = []
    for path in candidate_data_paths(explicit_path):
        if not path.exists() or not path.is_file():
            continue
        try:
            return path, load_ohlcv(path), errors
        except Exception as exc:  # noqa: BLE001 - diagnostics should keep scanning candidates.
            errors.append(f"{path}: {exc}")
    return None, None, errors


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    data = calculate_indicators(df).copy()
    data["baseline_entry_raw"] = (
        (data["close"] > data["ema200"])
        & (data["ema20"] > data["ema60"])
        & (data["rsi14"].between(45, 70))
    )
    data["baseline_exit"] = data["close"] < data["ema20"]
    # generate_signal() checks exit first, so long_entry cannot happen on an exit candle.
    data["baseline_entry"] = data["baseline_entry_raw"] & ~data["baseline_exit"]
    data["ema200_slope_12"] = data["ema200"] > data["ema200"].shift(12)
    data["anti_chase_ok"] = ((data["close"] - data["ema20"]) / data["atr14"]) <= 1.0
    data["anti_chase_ok"] = data["anti_chase_ok"] & (data["atr14"] > 0)
    data["confirmed_exit"] = data["baseline_exit"] & data["baseline_exit"].shift(1).fillna(False)
    return data.dropna(subset=["ema20", "ema60", "ema200", "rsi14", "atr14"]).reset_index(drop=True)


def entry_allowed(row: pd.Series, variant_name: str) -> bool:
    baseline = bool(row["baseline_entry"])
    if variant_name == "Variant A":
        return baseline and bool(row["ema200_slope_12"])
    if variant_name == "Variant B":
        return baseline and bool(row["anti_chase_ok"])
    return baseline


def exit_reason(row: pd.Series, variant_name: str, trailing_stop: Optional[float]) -> Optional[str]:
    if trailing_stop is not None and float(row["close"]) <= trailing_stop:
        return "atr_trailing_stop" if variant_name == "Variant E" else "stop_loss"
    if variant_name == "Variant D":
        return "confirmed_close_below_ema20" if bool(row["confirmed_exit"]) else None
    if bool(row["baseline_exit"]):
        return "close_below_ema20"
    return None


def estimate_equity(
    starting_equity: float,
    realized_pnl: float,
    entry_price: Optional[float],
    size: float,
    close: float,
) -> float:
    unrealized_pnl = 0.0
    if entry_price is not None and size > 0:
        unrealized_pnl = (close - entry_price) * size
    return starting_equity + realized_pnl + unrealized_pnl


def stop_distance(atr: float, atr_stop_multiplier: float) -> float:
    return max(float(atr) * atr_stop_multiplier, 0.0)


def position_size(
    equity: float,
    entry_price: float,
    atr: float,
    config: SimulationConfig,
) -> float:
    distance = stop_distance(atr, config.atr_stop_multiplier)
    if equity <= 0 or entry_price <= 0 or distance <= 0:
        return 0.0

    risk_budget = equity * config.max_risk_per_trade
    risk_based_size = risk_budget / distance
    max_affordable_size = (equity * 0.95) / entry_price
    return max(min(risk_based_size, max_affordable_size), 0.0)


def refresh_loss_windows(
    timestamp: pd.Timestamp,
    equity: float,
    state: dict[str, object],
) -> None:
    day = timestamp.date().isoformat()
    month = timestamp.strftime("%Y-%m")
    if state.get("daily_start_date") != day:
        state["daily_start_date"] = day
        state["daily_start_equity"] = equity
        state["daily_entries_blocked"] = False
    if state.get("monthly_start_month") != month and not state.get("monthly_entries_blocked"):
        state["monthly_start_month"] = month
        state["monthly_start_equity"] = equity
        state["monthly_entries_blocked"] = False


def can_enter_new_position(equity: float, state: dict[str, object], config: SimulationConfig) -> bool:
    daily_start = float(state.get("daily_start_equity") or equity or 0.0)
    monthly_start = float(state.get("monthly_start_equity") or equity or 0.0)
    if daily_start > 0 and (daily_start - equity) / daily_start >= config.max_daily_loss:
        state["daily_entries_blocked"] = True
    if monthly_start > 0 and (monthly_start - equity) / monthly_start >= config.max_monthly_loss:
        state["monthly_entries_blocked"] = True
    return not bool(state.get("daily_entries_blocked")) and not bool(
        state.get("monthly_entries_blocked")
    )


def simulate_variant_result(
    data: pd.DataFrame,
    variant: Variant,
    config: SimulationConfig,
) -> SimulationResult:
    realized_pnl = 0.0
    entry_equity = config.starting_equity
    entry_price: Optional[float] = None
    entry_fee = 0.0
    entry_index = 0
    entry_time: Optional[pd.Timestamp] = None
    size = 0.0
    trailing_stop: Optional[float] = None
    cooldown_until_index = -1
    trades: list[Trade] = []
    equity_curve: list[float] = []
    risk_state: dict[str, object] = {
        "daily_start_date": None,
        "daily_start_equity": config.starting_equity,
        "daily_entries_blocked": False,
        "monthly_start_month": None,
        "monthly_start_equity": config.starting_equity,
        "monthly_entries_blocked": False,
    }

    for index, row in data.iterrows():
        close = float(row["close"])
        atr14 = float(row["atr14"])
        timestamp = pd.Timestamp(row["timestamp"])
        equity = estimate_equity(config.starting_equity, realized_pnl, entry_price, size, close)
        refresh_loss_windows(timestamp, equity, risk_state)
        exited_this_candle = False

        if size > 0 and entry_price is not None:
            reason = exit_reason(row, variant.name, trailing_stop)
            if reason is not None:
                exit_price = close
                gross_pnl = (exit_price - entry_price) * size
                exit_fee = exit_price * size * config.fee_rate
                exit_net_pnl = gross_pnl - exit_fee
                realized_pnl += exit_net_pnl
                round_trip_pnl = exit_net_pnl - entry_fee
                trade_return = round_trip_pnl / entry_equity if entry_equity > 0 else 0.0
                trades.append(
                    Trade(
                        entry_time=entry_time or timestamp,
                        exit_time=timestamp,
                        entry_index=entry_index,
                        exit_index=index,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        trade_return=trade_return,
                        gross_pnl=gross_pnl,
                        fee_cost=entry_fee + exit_fee,
                        pnl=round_trip_pnl,
                        holding_candles=max(index - entry_index, 0),
                        exit_reason=reason,
                    )
                )
                size = 0.0
                entry_price = None
                entry_fee = 0.0
                trailing_stop = None
                exited_this_candle = True
                if variant.name == "Variant C":
                    cooldown_until_index = index + 3
            elif variant.name == "Variant E":
                candidate_stop = close - stop_distance(atr14, config.atr_stop_multiplier)
                trailing_stop = max(trailing_stop or candidate_stop, candidate_stop)

        equity = estimate_equity(config.starting_equity, realized_pnl, entry_price, size, close)
        if (
            size == 0
            and not exited_this_candle
            and index > cooldown_until_index
            and entry_allowed(row, variant.name)
            and can_enter_new_position(equity, risk_state, config)
        ):
            trade_size = position_size(equity, close, atr14, config)
            if trade_size > 0:
                entry_price = close
                size = trade_size
                entry_fee = close * size * config.fee_rate
                realized_pnl -= entry_fee
                entry_equity = equity
                entry_index = index
                entry_time = timestamp
                trailing_stop = close - stop_distance(atr14, config.atr_stop_multiplier)

        equity = estimate_equity(config.starting_equity, realized_pnl, entry_price, size, close)
        equity_curve.append(equity / config.starting_equity)

    if not equity_curve:
        return SimulationResult(
            variant=variant,
            metrics=empty_metrics(variant.name),
            trades=trades,
            equity_curve=equity_curve,
        )

    return SimulationResult(
        variant=variant,
        metrics=metrics_from_curve_and_trades(variant.name, equity_curve, trades),
        trades=trades,
        equity_curve=equity_curve,
    )


def simulate_variant(
    data: pd.DataFrame,
    variant: Variant,
    config: SimulationConfig,
) -> Metrics:
    return simulate_variant_result(data, variant, config).metrics


def empty_metrics(name: str) -> Metrics:
    return Metrics(
        name=name,
        total_return=0.0,
        max_drawdown=0.0,
        number_of_trades=0,
        win_rate=0.0,
        average_trade_return=0.0,
        profit_factor=None,
        average_holding_time=0.0,
        largest_loss=None,
        largest_win=None,
        whipsaw_count=0,
    )


def metrics_from_curve_and_trades(name: str, equity_curve: list[float], trades: list[Trade]) -> Metrics:
    curve = pd.Series(equity_curve, dtype="float64")
    total_return = float(curve.iloc[-1] - 1.0)
    running_max = curve.cummax()
    drawdown = curve / running_max - 1.0
    trade_returns = [trade.trade_return for trade in trades]
    wins = [trade for trade in trades if trade.pnl > 0]
    losses = [trade for trade in trades if trade.pnl < 0]
    profit_factor: Optional[float]
    if losses:
        profit_factor = sum(trade.pnl for trade in wins) / abs(
            sum(trade.pnl for trade in losses)
        ) if wins else 0.0
    elif wins:
        profit_factor = math.inf
    else:
        profit_factor = None

    return Metrics(
        name=name,
        total_return=total_return,
        max_drawdown=float(drawdown.min()),
        number_of_trades=len(trades),
        win_rate=(len(wins) / len(trades)) if trades else 0.0,
        average_trade_return=(sum(trade_returns) / len(trade_returns)) if trade_returns else 0.0,
        profit_factor=profit_factor,
        average_holding_time=(
            sum(trade.holding_candles for trade in trades) / len(trades) if trades else 0.0
        ),
        largest_loss=min(trade_returns) if trade_returns else None,
        largest_win=max(trade_returns) if trade_returns else None,
        whipsaw_count=sum(
            1 for trade in trades if trade.trade_return < 0 and trade.holding_candles <= 3
        ),
    )


def compare_to_baseline(metrics: list[Metrics]) -> None:
    baseline = next((item for item in metrics if item.name == "Baseline"), None)
    if baseline is None:
        return
    for item in metrics:
        if item.name == "Baseline":
            item.reduces_whipsaw = "baseline"
            item.reduces_overtrading = "baseline"
            continue
        item.reduces_whipsaw = yes_no(item.whipsaw_count < baseline.whipsaw_count)
        item.reduces_overtrading = yes_no(item.number_of_trades < baseline.number_of_trades)


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def format_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    if math.isinf(value):
        return "inf"
    return f"{value * 100:.2f}%"


def format_float(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    if math.isinf(value):
        return "inf"
    return f"{value:.2f}"


def print_table(metrics: list[Metrics]) -> None:
    headers = [
        "variant",
        "total_return",
        "max_dd",
        "trades",
        "win_rate",
        "avg_trade",
        "profit_factor",
        "avg_hold",
        "largest_loss",
        "largest_win",
        "less_whipsaw",
        "less_overtrade",
    ]
    rows = [
        [
            item.name,
            format_pct(item.total_return),
            format_pct(item.max_drawdown),
            str(item.number_of_trades),
            format_pct(item.win_rate),
            format_pct(item.average_trade_return),
            format_float(item.profit_factor),
            f"{item.average_holding_time:.1f}",
            format_pct(item.largest_loss),
            format_pct(item.largest_win),
            item.reduces_whipsaw,
            item.reduces_overtrading,
        ]
        for item in metrics
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def print_runtime_context() -> None:
    heartbeat_rows = read_csv_rows(HEARTBEAT_PATH)
    trade_rows = read_csv_rows(TRADES_PATH)
    paper_state = read_json(PAPER_STATE_PATH)
    paper_entries = sum(1 for row in trade_rows if row.get("action") == "entry")
    paper_exits = sum(1 for row in trade_rows if row.get("action") == "exit")
    print("Runtime context")
    print(f"- heartbeat rows: {len(heartbeat_rows)}")
    print(f"- paper trade entries/exits: {paper_entries}/{paper_exits}")
    print(f"- current paper position: {paper_state.get('current_simulated_position')}")
    print(f"- paper realized/unrealized PnL: {paper_state.get('realized_pnl')} / {paper_state.get('unrealized_pnl')}")


def print_missing_data_message(errors: list[str]) -> None:
    print("No local historical OHLCV data file was found, so no strategy comparison was run.")
    print("This script does not fetch remote candles and does not fake backtest results.")
    print()
    print("Provide a CSV or parquet file with at least these columns:")
    print("- timestamp, open, high, low, close, volume")
    print()
    print("Recommended locations or usage:")
    print("- data/BTCUSDT_1h.csv")
    print("- data/BTC_USDT_1h.csv")
    print("- python research\\compare_strategy_variants.py --data data\\YOUR_OHLCV_FILE.csv")
    if errors:
        print()
        print("Candidate files were found but rejected:")
        for error in errors:
            print(f"- {error}")


def load_assumptions() -> SimulationConfig:
    load_dotenv(ROOT / ".env")
    return SimulationConfig(
        starting_equity=parse_float_env("PAPER_STARTING_EQUITY", 10_000.0),
        fee_rate=parse_float_env("FEE_RATE", 0.001),
        slippage_rate_config=parse_float_env("SLIPPAGE_RATE", 0.0005),
        max_risk_per_trade=parse_float_env("MAX_RISK_PER_TRADE", 0.005),
        atr_stop_multiplier=parse_float_env("ATR_STOP_MULTIPLIER", 2.0),
        max_daily_loss=parse_float_env("MAX_DAILY_LOSS", 0.02),
        max_monthly_loss=parse_float_env("MAX_MONTHLY_LOSS", 0.10),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research-only comparison of candidate OKX BTC strategy variants."
    )
    parser.add_argument("--data", help="Path to a local OHLCV CSV/parquet file.", default=None)
    args = parser.parse_args()

    print("Strategy Variant Comparison")
    print("Research-only: no bot runtime, no orders, no live-trading changes.")
    print_runtime_context()
    print()

    simulation_config = load_assumptions()
    data_path, raw_data, errors = find_ohlcv_data(args.data)
    if raw_data is None or data_path is None:
        print_missing_data_message(errors)
        return

    data = prepare_data(raw_data)
    if data.empty:
        print("Historical OHLCV was loaded, but indicators were not ready after warmup.")
        print("Use a longer file, ideally at least 300 candles for EMA200 and ATR/RSI warmup.")
        return

    metrics = [
        simulate_variant(data, variant, simulation_config)
        for variant in VARIANTS
    ]
    compare_to_baseline(metrics)

    print(f"Data used: {data_path}")
    print(f"Rows loaded: {len(raw_data)}")
    print(f"Indicator-ready rows tested: {len(data)}")
    print(
        "Paper-compatible assumptions: "
        f"starting_equity={simulation_config.starting_equity}, "
        f"fee_rate={simulation_config.fee_rate}, "
        "effective_slippage=0.0"
    )
    print(
        "Risk assumptions: "
        f"max_risk_per_trade={simulation_config.max_risk_per_trade}, "
        f"atr_stop_multiplier={simulation_config.atr_stop_multiplier}, "
        f"max_daily_loss={simulation_config.max_daily_loss}, "
        f"max_monthly_loss={simulation_config.max_monthly_loss}"
    )
    print(
        "Slippage note: "
        f"SLIPPAGE_RATE config is {simulation_config.slippage_rate_config}, "
        "but dry-run paper trades currently fill at close without slippage."
    )
    print()
    print_table(metrics)
    print()
    print("Notes")
    print("- Whipsaw is counted as a losing completed trade held for 3 candles or fewer.")
    print("- Overtrading reduction means fewer completed trades than baseline.")
    print("- Results are research diagnostics only; they do not prove profitability or select a final strategy.")


if __name__ == "__main__":
    main()
