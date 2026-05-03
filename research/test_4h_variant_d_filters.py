from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.compare_strategy_variants import (
    SimulationConfig,
    Trade,
    can_enter_new_position,
    estimate_equity,
    format_float,
    format_pct,
    load_assumptions,
    load_ohlcv,
    position_size,
    prepare_data,
    refresh_loss_windows,
    stop_distance,
)


DEFAULT_DATA = ROOT / "data" / "BTCUSDT_4h.csv"


@dataclass(frozen=True)
class FilterSpec:
    name: str
    description: str
    atr_entry_percentile_max: Optional[float] = None
    exit_below_ema200: bool = False
    block_falling_ema200: bool = False


@dataclass
class FilterResult:
    spec: FilterSpec
    equity_curve: pd.Series
    trades: list[Trade]


FILTERS = [
    FilterSpec("D0", "Variant D unchanged."),
    FilterSpec("D1", "D plus no new entries when ATR14 percentile >= 70.", 0.70),
    FilterSpec("D2", "D plus no new entries when ATR14 percentile >= 60.", 0.60),
    FilterSpec("D3", "D plus exit if close < EMA200.", None, True),
    FilterSpec("D4", "D plus no new entries when EMA200 is falling.", None, False, True),
    FilterSpec(
        "D5",
        "D plus ATR p70 entry block and exit if close < EMA200.",
        0.70,
        True,
    ),
    FilterSpec(
        "D6",
        "D plus ATR p70 entry block and no entries when EMA200 is falling.",
        0.70,
        False,
        True,
    ),
]


def resolve_path(path_text: Optional[str]) -> Path:
    path = Path(path_text).expanduser() if path_text else DEFAULT_DATA
    if not path.is_absolute():
        path = ROOT / path
    return path


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        print("(no rows)")
        return
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def max_drawdown(curve: pd.Series) -> float:
    if curve.empty:
        return 0.0
    running_max = curve.cummax()
    return float((curve / running_max - 1.0).min())


def return_drawdown_ratio(total_return: float, max_dd: float) -> Optional[float]:
    if max_dd >= 0:
        return None
    return total_return / abs(max_dd)


def average(values: list[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def median(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return float(pd.Series(values).median())


def max_consecutive_losses(trades: list[Trade]) -> Optional[int]:
    if not trades:
        return None
    longest = 0
    current = 0
    for trade in trades:
        if trade.pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def time_in_market(trades: list[Trade], row_count: int) -> Optional[float]:
    if row_count <= 0:
        return None
    return sum(trade.holding_candles for trade in trades) / row_count


def profit_factor(trades: list[Trade]) -> Optional[float]:
    wins = [trade.pnl for trade in trades if trade.pnl > 0]
    losses = [trade.pnl for trade in trades if trade.pnl < 0]
    if losses:
        return sum(wins) / abs(sum(losses)) if wins else 0.0
    if wins:
        return math.inf
    return None


def monthly_returns(curve: pd.Series) -> pd.Series:
    if curve.empty:
        return pd.Series(dtype="float64")
    monthly_last = curve.resample("ME").last()
    return monthly_last.pct_change().fillna(monthly_last.iloc[0] - 1.0)


def annual_returns(curve: pd.Series) -> pd.Series:
    if curve.empty:
        return pd.Series(dtype="float64")
    annual_last = curve.resample("YE").last()
    return annual_last.pct_change().fillna(annual_last.iloc[0] - 1.0)


def entry_allowed(row: pd.Series, spec: FilterSpec) -> bool:
    if not bool(row["baseline_entry"]):
        return False
    if spec.atr_entry_percentile_max is not None:
        if float(row["atr_percentile"]) >= spec.atr_entry_percentile_max:
            return False
    if spec.block_falling_ema200 and not bool(row["ema200_slope_12"]):
        return False
    return True


def exit_reason(row: pd.Series, stop_price: Optional[float], spec: FilterSpec) -> Optional[str]:
    close = float(row["close"])
    if stop_price is not None and close <= stop_price:
        return "stop_loss"
    if spec.exit_below_ema200 and close < float(row["ema200"]):
        return "close_below_ema200"
    if bool(row["confirmed_exit"]):
        return "confirmed_close_below_ema20"
    return None


def simulate_filter(data: pd.DataFrame, spec: FilterSpec, config: SimulationConfig) -> FilterResult:
    realized_pnl = 0.0
    entry_equity = config.starting_equity
    entry_price: Optional[float] = None
    entry_fee = 0.0
    entry_index = 0
    entry_time: Optional[pd.Timestamp] = None
    size = 0.0
    stop_price: Optional[float] = None
    trades: list[Trade] = []
    equity_values: list[float] = []
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
            reason = exit_reason(row, stop_price, spec)
            if reason is not None:
                gross_pnl = (close - entry_price) * size
                exit_fee = close * size * config.fee_rate
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
                        exit_price=close,
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
                stop_price = None
                exited_this_candle = True

        equity = estimate_equity(config.starting_equity, realized_pnl, entry_price, size, close)
        if (
            size == 0
            and not exited_this_candle
            and entry_allowed(row, spec)
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
                stop_price = close - stop_distance(atr14, config.atr_stop_multiplier)

        equity = estimate_equity(config.starting_equity, realized_pnl, entry_price, size, close)
        equity_values.append(equity / config.starting_equity)

    return FilterResult(
        spec=spec,
        equity_curve=pd.Series(
            equity_values,
            index=pd.DatetimeIndex(data["timestamp"]),
            dtype="float64",
        ),
        trades=trades,
    )


def metrics_row(result: FilterResult, row_count: int) -> list[str]:
    curve = result.equity_curve
    total_return = float(curve.iloc[-1] - 1.0) if not curve.empty else 0.0
    dd = max_drawdown(curve)
    trades = result.trades
    trade_returns = [trade.trade_return for trade in trades]
    wins = [trade.trade_return for trade in trades if trade.pnl > 0]
    losses = [trade.trade_return for trade in trades if trade.pnl < 0]
    gross_pnl = sum(trade.gross_pnl for trade in trades)
    fees = sum(trade.fee_cost for trade in trades)
    net_pnl = sum(trade.pnl for trade in trades)
    return [
        result.spec.name,
        format_pct(total_return),
        format_pct(dd),
        format_float(return_drawdown_ratio(total_return, dd)),
        format_float(profit_factor(trades)),
        format_pct(len(wins) / len(trades) if trades else None),
        str(len(trades)),
        format_pct(average(trade_returns)),
        format_pct(average(wins)),
        format_pct(average(losses)),
        format_pct(max(wins) if wins else None),
        format_pct(min(losses) if losses else None),
        str(max_consecutive_losses(trades) if trades else "n/a"),
        f"{average([trade.holding_candles for trade in trades]):.1f}" if trades else "n/a",
        f"{median([trade.holding_candles for trade in trades]):.1f}" if trades else "n/a",
        f"{fees:.2f}",
        f"{gross_pnl:.2f}",
        f"{net_pnl:.2f}",
        format_pct(time_in_market(trades, row_count)),
    ]


def print_metrics(results: list[FilterResult], row_count: int) -> None:
    headers = [
        "variant",
        "total_return",
        "max_dd",
        "ret/dd",
        "profit_factor",
        "win_rate",
        "trades",
        "avg_trade",
        "avg_win",
        "avg_loss",
        "largest_win",
        "largest_loss",
        "loss_streak",
        "avg_hold",
        "median_hold",
        "fees",
        "gross_pnl",
        "net_pnl",
        "time_in_market",
    ]
    print_table(headers, [metrics_row(result, row_count) for result in results])


def print_best_worst_months(results: list[FilterResult]) -> None:
    headers = ["variant", "best_month", "best_return", "worst_month", "worst_return"]
    rows = []
    for result in results:
        monthly = monthly_returns(result.equity_curve)
        best = monthly.idxmax()
        worst = monthly.idxmin()
        rows.append(
            [
                result.spec.name,
                best.strftime("%Y-%m"),
                format_pct(float(monthly.loc[best])),
                worst.strftime("%Y-%m"),
                format_pct(float(monthly.loc[worst])),
            ]
        )
    print_table(headers, rows)


def print_yearly_returns(results: list[FilterResult]) -> None:
    annual_by_name = {result.spec.name: annual_returns(result.equity_curve) for result in results}
    years = sorted(set().union(*(series.index for series in annual_by_name.values())))
    headers = ["year"] + [result.spec.name for result in results]
    rows = []
    for year in years:
        row = [year.strftime("%Y")]
        for result in results:
            value = annual_by_name[result.spec.name].get(year)
            row.append(format_pct(float(value)) if value is not None and not pd.isna(value) else "n/a")
        rows.append(row)
    print_table(headers, rows)


def slice_data(data: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    return data[(data["timestamp"] >= start_ts) & (data["timestamp"] <= end_ts)].reset_index(drop=True)


def print_oos_splits(data: pd.DataFrame, config: SimulationConfig) -> None:
    headers = ["split", "variant", "total_return", "max_dd", "ret/dd", "trades", "profit_factor", "time_in_market"]
    rows = []
    splits = [
        ("2021-2023", "2021-01-01T00:00:00Z", "2023-12-31T23:59:59Z"),
        ("2024-2026", "2024-01-01T00:00:00Z", "2026-05-03T23:59:59Z"),
    ]
    for label, start, end in splits:
        split = slice_data(data, start, end)
        if split.empty:
            continue
        for spec in FILTERS:
            result = simulate_filter(split, spec, config)
            total_return = float(result.equity_curve.iloc[-1] - 1.0)
            dd = max_drawdown(result.equity_curve)
            rows.append(
                [
                    label,
                    spec.name,
                    format_pct(total_return),
                    format_pct(dd),
                    format_float(return_drawdown_ratio(total_return, dd)),
                    str(len(result.trades)),
                    format_float(profit_factor(result.trades)),
                    format_pct(time_in_market(result.trades, len(split))),
                ]
            )
    print_table(headers, rows)


def high_atr_trade_summary(data: pd.DataFrame, results: list[FilterResult]) -> None:
    headers = ["variant", "entries_high_atr_p70", "high_atr_gross", "high_atr_fees", "high_atr_net"]
    rows = []
    for result in results:
        trades = [
            trade
            for trade in result.trades
            if trade.entry_index < len(data) and data.iloc[trade.entry_index]["atr_percentile"] >= 0.70
        ]
        rows.append(
            [
                result.spec.name,
                str(len(trades)),
                f"{sum(trade.gross_pnl for trade in trades):.2f}",
                f"{sum(trade.fee_cost for trade in trades):.2f}",
                f"{sum(trade.pnl for trade in trades):.2f}",
            ]
        )
    print_table(headers, rows)


def add_filter_columns(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["atr_percentile"] = result["atr14"].rank(pct=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Research-only tests for 4h Variant D filters.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="4h OHLCV CSV/parquet path.")
    args = parser.parse_args()

    data_path = resolve_path(args.data)
    raw_data = load_ohlcv(data_path)
    data = add_filter_columns(prepare_data(raw_data))
    if data.empty:
        raise SystemExit(f"No indicator-ready rows in {data_path}")

    config = load_assumptions()
    results = [simulate_filter(data, spec, config) for spec in FILTERS]

    print("4h Variant D Filter Tests")
    print("Research-only: no bot runtime, no orders, no live-trading changes.")
    print(f"data path: {data_path}")
    print(f"rows loaded: {len(raw_data)}")
    print(f"indicator-ready rows tested: {len(data)}")
    print(f"tested range: {data['timestamp'].iloc[0]} -> {data['timestamp'].iloc[-1]}")
    print()
    print("Filter Definitions")
    print("------------------")
    for spec in FILTERS:
        print(f"{spec.name}: {spec.description}")

    print()
    print("Main Metrics")
    print("------------")
    print_metrics(results, len(data))

    print()
    print("Best/Worst Months")
    print("-----------------")
    print_best_worst_months(results)

    print()
    print("Yearly Returns")
    print("--------------")
    print_yearly_returns(results)

    print()
    print("Out-Of-Sample Splits")
    print("--------------------")
    print_oos_splits(data, config)

    print()
    print("High ATR Entry Diagnostics")
    print("--------------------------")
    high_atr_trade_summary(data, results)

    print()
    print("Notes")
    print("- D0 is the existing research Variant D.")
    print("- ATR percentile filters use the full loaded 4h research sample.")
    print("- These are diagnostics only; they do not prove profitability or select a final strategy.")


if __name__ == "__main__":
    main()
