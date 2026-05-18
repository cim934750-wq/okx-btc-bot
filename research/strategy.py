from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import FractionalBacktest

from research.config import BacktestConfig, StrategyParams
from research.indicators import build_feature_frame


class _BaseMTFStrategy(Strategy):
    starter_size = 0.25
    add_on_size = 0.15
    partial_exit_pct = 0.50
    cooldown_bars = 4
    direction_cooldown_bars = 3
    add_on_gap_bars = 3
    stop_atr_mult = 1.5
    tp1_rr = 1.0
    tp2_rr = 2.4
    trail_atr_mult = 2.25
    breakeven_offset_atr = 0.05
    add_on_profit_atr = 0.8
    use_broker_executable_long_tp1 = False
    long_tp1_leg_fraction = 0.5
    long_tp1_profit_lock_atr = 0.0
    long_tp2_profit_lock_rr = 0.0
    long_tp2_trail_atr_mult = 0.0
    enable_pyramiding = True
    allow_longs = True
    allow_shorts = True
    commission_rate = 0.0005
    runtime_price_scale = 1.0

    def init(self) -> None:
        self.highest_since_entry = np.nan
        self.lowest_since_entry = np.nan
        self.tp1_hit = False
        self.tp2_hit = False
        self.current_long_entry_bar = -10_000
        self.last_exit_bar = -10_000
        self.last_long_entry_bar = -10_000
        self.last_short_entry_bar = -10_000
        self.last_long_add_bar = -10_000
        self.last_short_add_bar = -10_000

    def _avg_entry_price(self) -> float:
        trades = [t for t in self.trades if t.is_long] if self.position.is_long else [t for t in self.trades if t.is_short]
        if not trades:
            return float("nan")
        notional = sum(abs(t.size) * t.entry_price for t in trades)
        total_size = sum(abs(t.size) for t in trades)
        if total_size == 0:
            return float("nan")
        return notional / total_size

    # FractionalBacktest scales runtime OHLC/order prices, while indicator
    # ATR/EMA values stay in original market-price units. Use the distance
    # helper only for ATR-derived distances and the price-level helper only
    # for indicator price levels such as EMA. Do not pass already runtime-
    # scaled Close/High/Low, entry, or avg_entry values into either helper.
    def _to_runtime_distance(self, unscaled_distance: float) -> float:
        return unscaled_distance * self.runtime_price_scale

    def _to_runtime_price_level(self, unscaled_price: float) -> float:
        return unscaled_price * self.runtime_price_scale

    def _reset_state_if_flat(self) -> None:
        if not self.position:
            self.highest_since_entry = np.nan
            self.lowest_since_entry = np.nan
            self.tp1_hit = False
            self.tp2_hit = False
            self.current_long_entry_bar = -10_000

    def _long_entry_ready(self, i: int) -> bool:
        return (
            self.allow_longs
            and i - self.last_exit_bar >= self.cooldown_bars
            and i - self.last_long_entry_bar >= self.direction_cooldown_bars
        )

    def _enter_long(self, i: int) -> None:
        if self.use_broker_executable_long_tp1:
            entry_ref = float(self.data.Close[-1])
            risk = self._to_runtime_distance(float(self.data.atr[-1]) * self.stop_atr_mult)
            raw_sl_price = entry_ref - risk
            sl_price = raw_sl_price if np.isfinite(raw_sl_price) and raw_sl_price > 0 else None
            tp1_price = entry_ref + risk * self.tp1_rr
            tp1_size = self.starter_size * self.long_tp1_leg_fraction
            runner_size = self.starter_size - tp1_size
            if tp1_size > 0:
                self.buy(size=tp1_size, sl=sl_price, tp=tp1_price, tag="Long1_TP1")
            if runner_size > 0:
                self.buy(size=runner_size, sl=sl_price, tag="Long1_Run")
        else:
            self.buy(size=self.starter_size, tag="Long1")
        self.last_long_entry_bar = i
        self.current_long_entry_bar = i
        self.highest_since_entry = self.data.High[-1]
        self.tp1_hit = False
        self.tp2_hit = False

    def _update_extremes(self) -> None:
        if self.position.is_long:
            self.highest_since_entry = self.data.High[-1] if np.isnan(self.highest_since_entry) else max(self.highest_since_entry, self.data.High[-1])
        elif self.position.is_short:
            self.lowest_since_entry = self.data.Low[-1] if np.isnan(self.lowest_since_entry) else min(self.lowest_since_entry, self.data.Low[-1])

    def _manage_long(self, i: int) -> None:
        avg_entry = self._avg_entry_price()
        atr = float(self.data.atr[-1])
        runtime_atr = self._to_runtime_distance(atr)
        risk = runtime_atr * self.stop_atr_mult
        tp1 = avg_entry + risk * self.tp1_rr
        tp2 = avg_entry + risk * self.tp2_rr
        base_stop = avg_entry - risk
        round_trip_fee_buffer = avg_entry * self.commission_rate * 2.0
        tp1_floor = avg_entry + round_trip_fee_buffer + runtime_atr * self.breakeven_offset_atr
        if self.long_tp1_profit_lock_atr > 0:
            tp1_floor = max(
                tp1_floor,
                avg_entry + round_trip_fee_buffer + runtime_atr * self.long_tp1_profit_lock_atr,
            )

        if self.use_broker_executable_long_tp1:
            self.tp1_hit = self.tp1_hit or any(
                trade.tag == "Long1_TP1" and trade.entry_bar >= self.current_long_entry_bar
                for trade in self.closed_trades
            )
        elif not self.tp1_hit and self.data.High[-1] >= tp1:
            self.position.close(portion=self.partial_exit_pct)
            self.tp1_hit = True

        if not self.tp2_hit and self.data.High[-1] >= tp2:
            self.tp2_hit = True

        break_even = tp1_floor if self.tp1_hit else base_stop
        active_trail_mult = self.long_tp2_trail_atr_mult if (self.tp2_hit and self.long_tp2_trail_atr_mult > 0) else self.trail_atr_mult
        trail_raw = (
            self.highest_since_entry - runtime_atr * active_trail_mult
            if not np.isnan(self.highest_since_entry)
            else base_stop
        )
        runner_stop = max(break_even, trail_raw)
        if self.tp2_hit and self.long_tp2_profit_lock_rr > 0:
            tp2_floor = avg_entry + round_trip_fee_buffer + risk * self.long_tp2_profit_lock_rr
            runner_stop = max(runner_stop, tp2_floor)
        runtime_ema50 = self._to_runtime_price_level(float(self.data.ema50[-1]))
        trend_fail = (self.data.Close[-1] < runtime_ema50 and self.data.minus_di[-1] > self.data.plus_di[-1]) or (not self.data.weekly_bull[-1]) or (not self.data.daily_bull[-1])

        safe_long_stop = runner_stop if np.isfinite(runner_stop) and runner_stop > 0 else None
        for trade in self.trades:
            if trade.is_long and safe_long_stop is not None and (
                not self.use_broker_executable_long_tp1 or trade.tag == "Long1_Run"
            ):
                trade.sl = safe_long_stop

        if trend_fail:
            self.position.close()
            return

    def _manage_short(self, i: int) -> None:
        avg_entry = self._avg_entry_price()
        atr = float(self.data.atr[-1])
        runtime_atr = self._to_runtime_distance(atr)
        risk = runtime_atr * self.stop_atr_mult
        tp1 = avg_entry - risk * self.tp1_rr
        tp2 = avg_entry - risk * self.tp2_rr
        base_stop = avg_entry + risk
        break_even = avg_entry - runtime_atr * self.breakeven_offset_atr if self.tp1_hit else base_stop
        trail_raw = self.lowest_since_entry + runtime_atr * self.trail_atr_mult if not np.isnan(self.lowest_since_entry) else base_stop
        runner_stop = min(break_even, trail_raw)
        runtime_ema50 = self._to_runtime_price_level(float(self.data.ema50[-1]))
        trend_fail = (self.data.Close[-1] > runtime_ema50 and self.data.plus_di[-1] > self.data.minus_di[-1]) or (not self.data.weekly_bear[-1]) or (not self.data.daily_bear[-1])

        # Keep short stops as live stop orders so large reversal bars are handled
        # more like hard stops instead of waiting for close-based liquidation.
        for trade in self.trades:
            if trade.is_short:
                trade.sl = runner_stop

        if (not self.tp1_hit) and self.data.Low[-1] <= tp1:
            self.position.close(portion=self.partial_exit_pct)
            self.tp1_hit = True
        if trend_fail:
            self.position.close()
            self.last_exit_bar = i
            return
        if self.data.Low[-1] <= tp2:
            self.position.close()
            self.last_exit_bar = i

    def next(self) -> None:
        i = len(self.data.Close) - 1
        self._reset_state_if_flat()
        self._update_extremes()

        if self.position.is_long:
            self._manage_long(i)
        elif self.position.is_short:
            self._manage_short(i)

        if not self.position:
            if self.allow_longs and self.data.starter_long_signal[-1] and self._long_entry_ready(i):
                self._enter_long(i)
            elif self.allow_shorts and self.data.starter_short_signal[-1] and i - self.last_exit_bar >= self.cooldown_bars and i - self.last_short_entry_bar >= self.direction_cooldown_bars:
                self.sell(size=self.starter_size, tag="Short1")
                self.last_short_entry_bar = i
                self.lowest_since_entry = self.data.Low[-1]
                self.tp1_hit = False
                self.tp2_hit = False
            return

        if self.allow_longs and self.enable_pyramiding and self.position.is_long and len(self.trades) < 2:
            avg_entry = self._avg_entry_price()
            add_on_profit_distance = self._to_runtime_distance(float(self.data.atr[-1]) * self.add_on_profit_atr)
            in_profit = self.data.Close[-1] > avg_entry + add_on_profit_distance
            if self.data.add_long_signal[-1] and in_profit and i - self.last_long_add_bar >= self.add_on_gap_bars:
                self.buy(size=self.add_on_size, tag="Long2")
                self.last_long_add_bar = i

        if self.allow_shorts and self.enable_pyramiding and self.position.is_short and len(self.trades) < 2:
            avg_entry = self._avg_entry_price()
            add_on_profit_distance = self._to_runtime_distance(float(self.data.atr[-1]) * self.add_on_profit_atr)
            in_profit = self.data.Close[-1] < avg_entry - add_on_profit_distance
            if self.data.add_short_signal[-1] and in_profit and i - self.last_short_add_bar >= self.add_on_gap_bars:
                self.sell(size=self.add_on_size, tag="Short2")
                self.last_short_add_bar = i


def make_strategy_class(params: StrategyParams, bt_config: BacktestConfig) -> type[_BaseMTFStrategy]:
    attrs: dict[str, Any] = {
        "starter_size": bt_config.starter_size,
        "add_on_size": bt_config.add_on_size,
        "partial_exit_pct": bt_config.partial_exit_pct,
        "cooldown_bars": params.cooldown_bars,
        "direction_cooldown_bars": params.direction_cooldown_bars,
        "add_on_gap_bars": params.add_on_gap_bars,
        "stop_atr_mult": params.stop_atr_mult,
        "tp1_rr": params.tp1_rr,
        "tp2_rr": params.tp2_rr,
        "trail_atr_mult": params.trail_atr_mult,
        "breakeven_offset_atr": params.breakeven_offset_atr,
        "add_on_profit_atr": params.add_on_profit_atr,
        "use_broker_executable_long_tp1": params.use_broker_executable_long_tp1,
        "long_tp1_leg_fraction": params.long_tp1_leg_fraction,
        "long_tp1_profit_lock_atr": params.long_tp1_profit_lock_atr,
        "long_tp2_profit_lock_rr": params.long_tp2_profit_lock_rr,
        "long_tp2_trail_atr_mult": params.long_tp2_trail_atr_mult,
        "enable_pyramiding": bt_config.enable_add_on_entries and bt_config.add_on_size > 0,
        "allow_longs": bt_config.allow_longs,
        "allow_shorts": bt_config.allow_shorts,
        "commission_rate": bt_config.commission,
    }
    return type("MTFTrendPullbackStrategy", (_BaseMTFStrategy,), attrs)


def run_backtest(
    raw_df: pd.DataFrame,
    params: StrategyParams,
    bt_config: BacktestConfig,
) -> tuple[pd.Series, pd.DataFrame]:
    frame = build_feature_frame(raw_df, params)
    frame = frame.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    bt_class = FractionalBacktest if FractionalBacktest is not None else Backtest
    runtime_price_scale = (1 / 100e6) if bt_class is FractionalBacktest else 1.0
    strategy_cls = type(
        "MTFTrendPullbackStrategyRuntime",
        (make_strategy_class(params, bt_config),),
        {"runtime_price_scale": runtime_price_scale},
    )
    bt = bt_class(
        frame,
        strategy_cls,
        cash=bt_config.initial_cash,
        commission=bt_config.commission,
        trade_on_close=bt_config.trade_on_close,
        exclusive_orders=bt_config.exclusive_orders,
        hedging=bt_config.hedging,
    )
    stats = bt.run()
    trades = stats["_trades"].copy()
    return stats, trades


def extract_metrics(stats: pd.Series, trades: pd.DataFrame) -> dict[str, float]:
    equity_curve = stats.get("_equity_curve")
    if isinstance(equity_curve, pd.DataFrame) and "Equity" in equity_curve.columns and not equity_curve.empty:
        equity_initial = float(equity_curve["Equity"].iloc[0])
        equity_final = float(equity_curve["Equity"].iloc[-1])
    else:
        equity_initial = float(stats.get("Equity Initial [$]", 0.0))
        equity_final = float(stats.get("Equity Final [$]", 0.0))

    if trades.empty:
        return {
            "net_profit": float(equity_final - equity_initial),
            "profit_factor": 0.0,
            "max_drawdown_pct": abs(float(stats.get("Max. Drawdown [%]", 0.0))),
            "total_trades": 0.0,
            "percent_profitable": 0.0,
            "avg_trade": 0.0,
            "expectancy": 0.0,
        }

    pnl = trades["PnL"].astype(float)
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = -pnl[pnl < 0].sum()
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    avg_trade = float(pnl.mean())
    win_rate = float((pnl > 0).mean() * 100.0)
    expectancy = avg_trade
    net_profit = float(equity_final - equity_initial)
    return {
        "net_profit": net_profit,
        "profit_factor": float(profit_factor),
        "max_drawdown_pct": abs(float(stats["Max. Drawdown [%]"])),
        "total_trades": float(len(trades)),
        "percent_profitable": win_rate,
        "avg_trade": avg_trade,
        "expectancy": expectancy,
    }


def metrics_with_params(params: StrategyParams, stats: pd.Series, trades: pd.DataFrame) -> dict[str, Any]:
    metrics = extract_metrics(stats, trades)
    metrics.update(asdict(params))
    return metrics
