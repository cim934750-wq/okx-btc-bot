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
    VARIANTS,
    SimulationResult,
    Trade,
    Variant,
    format_float,
    format_pct,
    load_assumptions,
    load_ohlcv,
    prepare_data,
    simulate_variant_result,
)


DEFAULT_DATA = ROOT / "data" / "BTCUSDT_4h.csv"
SELECTED_VARIANTS = {"Baseline", "Variant C", "Variant D"}


@dataclass(frozen=True)
class SeriesResult:
    name: str
    curve: pd.Series
    trades: list[Trade]
    metrics: dict[str, object]


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
    return sum(max(trade.holding_candles, 0) for trade in trades) / row_count


def median_holding(trades: list[Trade]) -> Optional[float]:
    if not trades:
        return None
    return float(pd.Series([trade.holding_candles for trade in trades]).median())


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


def buy_hold_curve(data: pd.DataFrame) -> pd.Series:
    close = data["close"].astype(float)
    curve = close / close.iloc[0]
    return pd.Series(curve.to_numpy(), index=pd.DatetimeIndex(data["timestamp"]), dtype="float64")


def curve_from_result(data: pd.DataFrame, result: SimulationResult) -> pd.Series:
    return pd.Series(
        result.equity_curve,
        index=pd.DatetimeIndex(data["timestamp"]),
        dtype="float64",
    )


def build_results(data: pd.DataFrame) -> list[SeriesResult]:
    config = load_assumptions()
    results = [
        simulate_variant_result(data, variant, config)
        for variant in VARIANTS
        if variant.name in SELECTED_VARIANTS
    ]
    by_name = {result.variant.name: result for result in results}
    ordered = [by_name[name] for name in ["Baseline", "Variant C", "Variant D"]]

    series_results = [
        SeriesResult(
            name="Buy & Hold",
            curve=buy_hold_curve(data),
            trades=[],
            metrics={},
        )
    ]
    for result in ordered:
        series_results.append(
            SeriesResult(
                name=result.variant.name,
                curve=curve_from_result(data, result),
                trades=result.trades,
                metrics={"profit_factor": result.metrics.profit_factor},
            )
        )
    return series_results


def metrics_row(result: SeriesResult, row_count: int) -> list[str]:
    curve = result.curve
    total_return = float(curve.iloc[-1] - 1.0) if not curve.empty else 0.0
    dd = max_drawdown(curve)
    trades = result.trades
    trade_returns = [trade.trade_return for trade in trades]
    wins = [trade.trade_return for trade in trades if trade.pnl > 0]
    losses = [trade.trade_return for trade in trades if trade.pnl < 0]
    gross_pnl = sum(trade.gross_pnl for trade in trades)
    fees = sum(trade.fee_cost for trade in trades)
    net_pnl = sum(trade.pnl for trade in trades)
    profit_factor = result.metrics.get("profit_factor") if result.metrics else None

    return [
        result.name,
        format_pct(total_return),
        format_pct(dd),
        format_float(return_drawdown_ratio(total_return, dd)),
        format_float(profit_factor if isinstance(profit_factor, float) else None),
        format_pct(len(wins) / len(trades) if trades else None),
        str(len(trades)) if trades else "n/a",
        format_pct(average(trade_returns)),
        format_pct(average(wins)),
        format_pct(average(losses)),
        format_pct(max(wins) if wins else None),
        format_pct(min(losses) if losses else None),
        str(max_consecutive_losses(trades) if trades else "n/a"),
        f"{average([trade.holding_candles for trade in trades]):.1f}" if trades else "n/a",
        f"{median_holding(trades):.1f}" if trades else "n/a",
        f"{fees:.2f}" if trades else "0.00",
        f"{gross_pnl:.2f}" if trades else "n/a",
        f"{net_pnl:.2f}" if trades else "n/a",
        format_pct(1.0 if result.name == "Buy & Hold" else time_in_market(trades, row_count)),
    ]


def print_metrics_table(results: list[SeriesResult], row_count: int) -> None:
    headers = [
        "name",
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
        "total_fees",
        "gross_pnl",
        "net_pnl",
        "time_in_market",
    ]
    print_table(headers, [metrics_row(result, row_count) for result in results])


def print_best_worst_months(results: list[SeriesResult]) -> None:
    headers = ["name", "best_month", "best_return", "worst_month", "worst_return"]
    rows = []
    for result in results:
        monthly = monthly_returns(result.curve)
        if monthly.empty:
            rows.append([result.name, "n/a", "n/a", "n/a", "n/a"])
            continue
        best_index = monthly.idxmax()
        worst_index = monthly.idxmin()
        rows.append(
            [
                result.name,
                best_index.strftime("%Y-%m"),
                format_pct(float(monthly.loc[best_index])),
                worst_index.strftime("%Y-%m"),
                format_pct(float(monthly.loc[worst_index])),
            ]
        )
    print_table(headers, rows)


def print_monthly_return_matrix(results: list[SeriesResult]) -> None:
    monthly_by_name = {result.name: monthly_returns(result.curve) for result in results}
    all_months = sorted(set().union(*(series.index for series in monthly_by_name.values())))
    headers = ["month"] + [result.name for result in results]
    rows = []
    for month in all_months:
        row = [month.strftime("%Y-%m")]
        for result in results:
            value = monthly_by_name[result.name].get(month)
            row.append(format_pct(float(value)) if value is not None and not pd.isna(value) else "n/a")
        rows.append(row)
    print_table(headers, rows)


def print_annual_return_matrix(results: list[SeriesResult]) -> None:
    annual_by_name = {result.name: annual_returns(result.curve) for result in results}
    all_years = sorted(set().union(*(series.index for series in annual_by_name.values())))
    headers = ["year"] + [result.name for result in results]
    rows = []
    for year in all_years:
        row = [year.strftime("%Y")]
        for result in results:
            value = annual_by_name[result.name].get(year)
            row.append(format_pct(float(value)) if value is not None and not pd.isna(value) else "n/a")
        rows.append(row)
    print_table(headers, rows)


def slice_data(data: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    return data[(data["timestamp"] >= start_ts) & (data["timestamp"] <= end_ts)].reset_index(drop=True)


def print_split_results(data: pd.DataFrame) -> None:
    headers = ["split", "name", "total_return", "max_dd", "ret/dd", "trades", "profit_factor", "time_in_market"]
    rows = []
    splits = [
        ("2021-2023", "2021-01-01T00:00:00Z", "2023-12-31T23:59:59Z"),
        ("2024-2026", "2024-01-01T00:00:00Z", "2026-05-03T23:59:59Z"),
    ]
    for label, start, end in splits:
        split = slice_data(data, start, end)
        if split.empty:
            continue
        for result in build_results(split):
            total_return = float(result.curve.iloc[-1] - 1.0)
            dd = max_drawdown(result.curve)
            profit_factor = result.metrics.get("profit_factor") if result.metrics else None
            rows.append(
                [
                    label,
                    result.name,
                    format_pct(total_return),
                    format_pct(dd),
                    format_float(return_drawdown_ratio(total_return, dd)),
                    str(len(result.trades)) if result.trades else "n/a",
                    format_float(profit_factor if isinstance(profit_factor, float) else None),
                    format_pct(1.0 if result.name == "Buy & Hold" else time_in_market(result.trades, len(split))),
                ]
            )
    print_table(headers, rows)


def year_regime_labels(data: pd.DataFrame) -> pd.Series:
    close_by_year = data.set_index("timestamp")["close"].resample("YE").last()
    annual = close_by_year.pct_change().fillna(close_by_year.iloc[0] / data["close"].iloc[0] - 1.0)
    labels: dict[int, str] = {}
    for timestamp, value in annual.items():
        if value > 0.20:
            labels[timestamp.year] = "bull_year"
        elif value < -0.20:
            labels[timestamp.year] = "bear_year"
        else:
            labels[timestamp.year] = "chop_year"
    return data["timestamp"].dt.year.map(labels)


def regime_labels(data: pd.DataFrame) -> dict[str, pd.Series]:
    atr_threshold = data["atr14"].quantile(0.70)
    return {
        "price_vs_ema200": data.apply(
            lambda row: "above_ema200" if row["close"] > row["ema200"] else "below_ema200",
            axis=1,
        ),
        "ema200_slope": data.apply(
            lambda row: "ema200_rising" if row["ema200_slope_12"] else "ema200_falling",
            axis=1,
        ),
        "atr_percentile": data.apply(
            lambda row: "high_atr_p70" if row["atr14"] >= atr_threshold else "low_mid_atr",
            axis=1,
        ),
        "year_regime": year_regime_labels(data),
    }


def compounded_return(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    return float((1.0 + values).prod() - 1.0)


def print_variant_d_regime_split(data: pd.DataFrame, variant_d: SeriesResult) -> None:
    strategy_returns = variant_d.curve.pct_change().fillna(0.0)
    labels_by_regime = regime_labels(data)
    headers = ["regime", "bucket", "strategy_return", "trades", "gross_pnl", "fees", "net_pnl"]
    rows = []
    for regime_name, labels in labels_by_regime.items():
        for bucket in sorted(labels.dropna().unique()):
            mask = labels == bucket
            mask_values = mask.to_numpy()
            trades = [
                trade
                for trade in variant_d.trades
                if trade.entry_index < len(labels) and labels.iloc[trade.entry_index] == bucket
            ]
            rows.append(
                [
                    regime_name,
                    str(bucket),
                    format_pct(compounded_return(strategy_returns.iloc[mask_values])),
                    str(len(trades)),
                    f"{sum(trade.gross_pnl for trade in trades):.2f}",
                    f"{sum(trade.fee_cost for trade in trades):.2f}",
                    f"{sum(trade.pnl for trade in trades):.2f}",
                ]
            )
    print_table(headers, rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Research-only 4h strategy deep dive.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="4h OHLCV CSV/parquet path.")
    args = parser.parse_args()

    data_path = resolve_path(args.data)
    raw_data = load_ohlcv(data_path)
    data = prepare_data(raw_data)
    if data.empty:
        raise SystemExit(f"No indicator-ready rows in {data_path}")

    results = build_results(data)
    variant_d = next(result for result in results if result.name == "Variant D")

    print("4h Variant Deep Dive")
    print("Research-only: no bot runtime, no orders, no live-trading changes.")
    print(f"data path: {data_path}")
    print(f"rows loaded: {len(raw_data)}")
    print(f"indicator-ready rows tested: {len(data)}")
    print(f"tested range: {data['timestamp'].iloc[0]} -> {data['timestamp'].iloc[-1]}")

    print()
    print("Risk And Trade Metrics")
    print("----------------------")
    print_metrics_table(results, len(data))

    print()
    print("Best/Worst Months")
    print("-----------------")
    print_best_worst_months(results)

    print()
    print("Monthly Returns")
    print("---------------")
    print_monthly_return_matrix(results)

    print()
    print("Annual Returns")
    print("--------------")
    print_annual_return_matrix(results)

    print()
    print("Out-Of-Sample Splits")
    print("--------------------")
    print_split_results(data)

    print()
    print("Variant D Regime Split")
    print("----------------------")
    print_variant_d_regime_split(data, variant_d)

    print()
    print("Notes")
    print("- Buy-and-hold has no modeled fees and is always 100% in market.")
    print("- Strategy trades use the current paper-compatible research simulator.")
    print("- Bull/chop/bear year labels are inferred from calendar-year buy-and-hold returns.")
    print("- These are diagnostics only; they do not prove profitability or select a final strategy.")


if __name__ == "__main__":
    main()
