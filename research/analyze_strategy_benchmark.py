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
    Metrics,
    SimulationResult,
    Trade,
    compare_to_baseline,
    format_pct,
    load_assumptions,
    load_ohlcv,
    prepare_data,
    print_table,
    simulate_variant_result,
)


DEFAULT_DATA = ROOT / "data" / "BTCUSDT_1h.csv"
DEFAULT_4H_DATA = ROOT / "data" / "BTCUSDT_4h.csv"


@dataclass(frozen=True)
class BuyHoldMetrics:
    total_return: float
    max_drawdown: float
    volatility: float
    first_timestamp: pd.Timestamp
    last_timestamp: pd.Timestamp


def resolve_path(path_text: Optional[str], default: Path) -> Path:
    path = Path(path_text).expanduser() if path_text else default
    if not path.is_absolute():
        path = ROOT / path
    return path


def max_drawdown(curve: pd.Series) -> float:
    running_max = curve.cummax()
    drawdown = curve / running_max - 1.0
    return float(drawdown.min())


def annualized_volatility(data: pd.DataFrame) -> float:
    returns = data["close"].pct_change().dropna()
    if returns.empty:
        return 0.0
    median_delta = data["timestamp"].diff().dropna().median()
    if pd.isna(median_delta) or median_delta <= pd.Timedelta(0):
        return float(returns.std())
    periods_per_year = pd.Timedelta(days=365.25) / median_delta
    return float(returns.std() * math.sqrt(float(periods_per_year)))


def buy_and_hold_metrics(data: pd.DataFrame) -> BuyHoldMetrics:
    close = data["close"].astype(float)
    curve = close / close.iloc[0]
    return BuyHoldMetrics(
        total_return=float(curve.iloc[-1] - 1.0),
        max_drawdown=max_drawdown(curve),
        volatility=annualized_volatility(data),
        first_timestamp=pd.Timestamp(data["timestamp"].iloc[0]),
        last_timestamp=pd.Timestamp(data["timestamp"].iloc[-1]),
    )


def run_results(data: pd.DataFrame) -> list[SimulationResult]:
    config = load_assumptions()
    results = [simulate_variant_result(data, variant, config) for variant in VARIANTS]
    compare_to_baseline([result.metrics for result in results])
    return results


def print_dataset_header(title: str, path: Path, raw_data: pd.DataFrame, data: pd.DataFrame) -> None:
    print()
    print(title)
    print("=" * len(title))
    print(f"data path: {path}")
    print(f"rows loaded: {len(raw_data)}")
    print(f"indicator-ready rows tested: {len(data)}")
    if not data.empty:
        print(f"tested range: {data['timestamp'].iloc[0]} -> {data['timestamp'].iloc[-1]}")


def print_buy_hold_table(buy_hold: BuyHoldMetrics) -> None:
    headers = ["benchmark", "total_return", "max_dd", "volatility", "first", "last"]
    row = [
        "Buy & Hold",
        format_pct(buy_hold.total_return),
        format_pct(buy_hold.max_drawdown),
        format_pct(buy_hold.volatility),
        str(buy_hold.first_timestamp),
        str(buy_hold.last_timestamp),
    ]
    print_table_rows(headers, [row])


def print_variant_vs_buy_hold(results: list[SimulationResult], buy_hold: BuyHoldMetrics) -> None:
    headers = [
        "variant",
        "strategy_return",
        "buy_hold_return",
        "excess_return",
        "strategy_max_dd",
        "buy_hold_max_dd",
        "beats_bh",
    ]
    rows = []
    for result in results:
        metrics = result.metrics
        rows.append(
            [
                metrics.name,
                format_pct(metrics.total_return),
                format_pct(buy_hold.total_return),
                format_pct(metrics.total_return - buy_hold.total_return),
                format_pct(metrics.max_drawdown),
                format_pct(buy_hold.max_drawdown),
                "yes" if metrics.total_return > buy_hold.total_return else "no",
            ]
        )
    print_table_rows(headers, rows)


def max_consecutive_losses(trades: list[Trade]) -> int:
    longest = 0
    current = 0
    for trade in trades:
        if trade.pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def average(values: list[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def months_in_sample(data: pd.DataFrame) -> float:
    start = pd.Timestamp(data["timestamp"].iloc[0])
    end = pd.Timestamp(data["timestamp"].iloc[-1])
    days = max((end - start).total_seconds() / 86_400, 1.0)
    return max(days / 30.4375, 1 / 30.4375)


def median_holding(trades: list[Trade]) -> float:
    if not trades:
        return 0.0
    return float(pd.Series([trade.holding_candles for trade in trades]).median())


def print_trade_diagnostics(results: list[SimulationResult], data: pd.DataFrame) -> None:
    headers = [
        "variant",
        "avg_hold",
        "median_hold",
        "avg_win",
        "avg_loss",
        "largest_win",
        "largest_loss",
        "max_loss_streak",
        "trades/mo",
        "gross_pnl",
        "fees",
        "net_pnl",
    ]
    months = months_in_sample(data)
    rows = []
    for result in results:
        trades = result.trades
        wins = [trade.trade_return for trade in trades if trade.pnl > 0]
        losses = [trade.trade_return for trade in trades if trade.pnl < 0]
        gross_pnl = sum(trade.gross_pnl for trade in trades)
        fees = sum(trade.fee_cost for trade in trades)
        net_pnl = sum(trade.pnl for trade in trades)
        rows.append(
            [
                result.metrics.name,
                f"{result.metrics.average_holding_time:.1f}",
                f"{median_holding(trades):.1f}",
                format_pct(average(wins)),
                format_pct(average(losses)),
                format_pct(max(wins) if wins else None),
                format_pct(min(losses) if losses else None),
                str(max_consecutive_losses(trades)),
                f"{len(trades) / months:.1f}",
                f"{gross_pnl:.2f}",
                f"{fees:.2f}",
                f"{net_pnl:.2f}",
            ]
        )
    print_table_rows(headers, rows)


def regime_labels(data: pd.DataFrame) -> dict[str, pd.Series]:
    atr_median = data["atr14"].median()
    return {
        "price_vs_ema200": data.apply(
            lambda row: "above_ema200" if row["close"] > row["ema200"] else "below_ema200",
            axis=1,
        ),
        "ema200_slope": data.apply(
            lambda row: "ema200_rising" if row["ema200_slope_12"] else "ema200_falling",
            axis=1,
        ),
        "atr_volatility": data.apply(
            lambda row: "high_atr" if row["atr14"] >= atr_median else "low_atr",
            axis=1,
        ),
    }


def compounded_return(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    return float((1.0 + values).prod() - 1.0)


def regime_rows(results: list[SimulationResult], data: pd.DataFrame) -> list[list[str]]:
    labels_by_regime = regime_labels(data)
    rows = []
    for result in results:
        curve = pd.Series(result.equity_curve, dtype="float64")
        strategy_returns = curve.pct_change().fillna(0.0)
        for regime_name, labels in labels_by_regime.items():
            for bucket in sorted(labels.dropna().unique()):
                mask = labels == bucket
                trade_count = sum(
                    1
                    for trade in result.trades
                    if trade.entry_index < len(labels) and labels.iloc[trade.entry_index] == bucket
                )
                net_pnl = sum(
                    trade.pnl
                    for trade in result.trades
                    if trade.entry_index < len(labels) and labels.iloc[trade.entry_index] == bucket
                )
                rows.append(
                    [
                        result.metrics.name,
                        regime_name,
                        str(bucket),
                        format_pct(compounded_return(strategy_returns[mask])),
                        str(trade_count),
                        f"{net_pnl:.2f}",
                    ]
                )
    return rows


def parse_percent_text(value: str) -> float:
    return float(value.rstrip("%")) / 100


def print_regime_split(results: list[SimulationResult], data: pd.DataFrame) -> None:
    headers = ["variant", "regime", "bucket", "strategy_return", "trades", "net_pnl"]
    rows = regime_rows(results, data)
    print_table_rows(headers, rows)

    baseline_return_rows = [row for row in rows if row[0] == "Baseline"]
    if baseline_return_rows:
        worst_return = min(baseline_return_rows, key=lambda row: parse_percent_text(row[3]))
        print(
            "Baseline worst candle regime by strategy return: "
            f"{worst_return[1]}={worst_return[2]} ({worst_return[3]})"
        )

    baseline_rows = [
        row for row in rows if row[0] == "Baseline" and row[4] != "0"
    ]
    if baseline_rows:
        worst = min(baseline_rows, key=lambda row: float(row[5]))
        print(
            "Baseline worst trade-entry regime by completed net PnL: "
            f"{worst[1]}={worst[2]} ({worst[5]} USDT, {worst[4]} trades)"
        )


def print_table_rows(headers: list[str], rows: list[list[str]]) -> None:
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    print(" | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def analyze_dataset(path: Path, title: str, *, detailed: bool) -> tuple[list[SimulationResult], BuyHoldMetrics]:
    raw_data = load_ohlcv(path)
    data = prepare_data(raw_data)
    if data.empty:
        raise ValueError(f"{path} has no indicator-ready rows")

    results = run_results(data)
    buy_hold = buy_and_hold_metrics(data)
    print_dataset_header(title, path, raw_data, data)
    print()
    print("Variant Comparison")
    print("------------------")
    print_table([result.metrics for result in results])
    print()
    print("Buy-And-Hold Benchmark")
    print("----------------------")
    print_buy_hold_table(buy_hold)
    print()
    print("Variant Vs Buy-And-Hold")
    print("-----------------------")
    print_variant_vs_buy_hold(results, buy_hold)

    if detailed:
        print()
        print("Trade Diagnostics")
        print("-----------------")
        print_trade_diagnostics(results, data)
        print()
        print("Regime Split")
        print("------------")
        print_regime_split(results, data)

    return results, buy_hold


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research-only benchmark, trade, regime, and timeframe diagnostics."
    )
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="Primary OHLCV CSV/parquet path.")
    parser.add_argument(
        "--compare-4h",
        default=str(DEFAULT_4H_DATA),
        help="Optional 4h OHLCV CSV/parquet path to include if present.",
    )
    args = parser.parse_args()

    print("Strategy Benchmark Diagnostics")
    print("Research-only: no bot runtime, no orders, no live-trading changes.")
    primary_path = resolve_path(args.data, DEFAULT_DATA)
    analyze_dataset(primary_path, "Primary Dataset Analysis", detailed=True)

    four_hour_path = resolve_path(args.compare_4h, DEFAULT_4H_DATA)
    if four_hour_path.exists() and four_hour_path != primary_path:
        analyze_dataset(four_hour_path, "4h Dataset Comparison", detailed=False)
    elif not four_hour_path.exists():
        print()
        print("4h Dataset Comparison")
        print("=====================")
        print(f"4h data file not found: {four_hour_path}")

    print()
    print("Notes")
    print("- Buy-and-hold uses the same indicator-ready date span as the strategy test.")
    print("- Regime returns are compounded from strategy equity changes on candles in each bucket.")
    print("- Regime trade counts and PnL are assigned by each trade's entry candle.")
    print("- These are diagnostics only; they do not prove profitability or select a final strategy.")


if __name__ == "__main__":
    main()
