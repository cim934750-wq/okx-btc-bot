# Regime-Filtered Long-Only Definition Plan Round 1

## Purpose

This is a research-only frozen-definition plan for one future executable active candidate: `regime-filtered long-only candidate`. It exists because `multi_hypothesis_tournament_round1` found that active candidates were not executable from the prior plan: the regime-filtered candidate lacked an exact classifier, lookback, and allowed state.

This is not validation execution. It does not run a backtest, fetch OHLCV, change production source code, change production parameters, optimize, restart dry-run, create live trading plans, or claim implementation readiness.

## Context

The prior active strategy chain failed or was parked:

- Long1-only holdout failed: net PnL `-69.89`, PF `0.9832`, BTCUSDT `-50.21`, BTC PF `0.8475`.
- D2 dry-run reference failed: approximately `-51.92 USDT`.
- D6 early-stop dry-run failed: `-103.78 USDT`.
- 6-candle cooldown validation failed: net PnL `-91.46`, PF `0.9725`, BTCUSDT `-73.14`, PF `0.7461`.
- Anti-chase validation failed: net PnL `-225.26`, PF `0.9445`, BTCUSDT `-82.62`, PF `0.7259`.
- BTC-only immediate path was paused with decision `pause_no_trade_default`.
- Multi-hypothesis tournament result: `all_active_candidates_not_executable_keep_no_trade_default`.

No-trade / capital preservation remains the default. The bot service should remain stopped.

## Candidate Definition

The candidate is a fresh research hypothesis, not a revival of Long1-only as an implementation candidate. It uses a long-only structure corresponding to the prior Long1-style research baseline, but it allows new long entries only when the BTCUSDT 4h regime is `risk_on`.

Frozen candidate switches for future validation:

- `allow_longs = True`
- `allow_shorts = False`
- `enable_add_on_entries = False`
- Long2 disabled
- Short1 disabled
- Short2 disabled
- no production parameter changes
- no source changes except a future research-only diagnostic runner if explicitly approved

## Frozen Regime Formula

Regime anchor: `BTCUSDT_4h.csv` only.

For each closed BTCUSDT 4h candle:

1. Compute `btc_ema200 = EMA(BTCUSDT close, period=200, adjust=False, min_periods=200)`.
2. Compute `ema200_slope_24 = btc_ema200[t] - btc_ema200[t - 24]`.
3. Compute `rolling_high_180 = rolling max(BTCUSDT close, 180 candles, min_periods=180)`.
4. Compute `drawdown_from_rolling_high_pct = (BTCUSDT close / rolling_high_180 - 1) * 100`.
5. Set `risk_on = True` only when all are true:
   - `BTCUSDT close > btc_ema200`
   - `ema200_slope_24 > 0`
   - `drawdown_from_rolling_high_pct >= -20.0`
6. Otherwise set `risk_on = False`.

Warmup rule: if EMA200, slope, or rolling high is unavailable, regime is `risk_off` and entries are blocked.

Why these values are structural, not optimized:

- EMA200 is a standard broad trend filter and was chosen before validation.
- A 24-candle slope lookback equals 4 days of 4h candles and checks that the broad trend is not merely above EMA200 but rising.
- A 180-candle rolling high equals roughly 30 days of 4h candles and is used only to identify severe drawdown context.
- A 20% drawdown threshold is a conservative crypto drawdown guard, not a fitted threshold.

## Entry Blocking Behavior

If `risk_on` is false for the aligned BTCUSDT regime candle, block all new long entries for that market candle. Because `enable_add_on_entries = False`, this candidate only concerns starter long entries in future validation.

The filter does not force-exit open positions. Existing exits, stops, trailing behavior, breakeven behavior, sizing, commissions, and all non-entry management logic remain unchanged from the final unit-fixed research source.

## Data Alignment Rules

- All timestamps are interpreted as UTC closed-candle timestamps.
- BTCUSDT regime is computed only from BTCUSDT 4h closed candles.
- For each market candle, use the BTCUSDT regime value at the same timestamp if present.
- If the exact BTCUSDT timestamp is missing, use the most recent prior BTCUSDT 4h closed candle at or before the market candle timestamp.
- Never use a future BTCUSDT candle.
- If no prior BTCUSDT candle exists, or if BTCUSDT regime fields are in warmup/missing state, classify as `risk_off` and block new entries.
- BTCUSDT itself uses the same regime filter.
- `BTCUSDT_1h.csv` is excluded.

## Future Validation Data Scope

- Same 19 local 4h markets where applicable: AAVE, ADA, ATOM, AVAX, BCH, BNB, BTC, DOGE, DOT, ETC, ETH, FIL, LINK, LTC, NEAR, SOL, TRX, UNI, XRP.
- Chronological 70/30 split consistent with prior holdout validation.
- BTCUSDT visible.
- DOGE, DOT, and UNI visible.
- No new OHLCV unless separately approved before validation.
- No fake or inferred data.
- No post-result market removal.

## Required Future Metrics

Future validation must report net PnL, PF, max DD, win rate, trade count, blocked entries, blocked entries by regime reason, active-regime exposure, BTCUSDT result, DOGE/DOT/UNI result, no-trade comparison, buy-and-hold BTC comparison, failed-reference comparison, and concentration.

## Pass / Fail Boundary

A future validation pass requires the candidate to beat no-trade after fees, produce positive aggregate holdout PnL, PF >= 1.10, BTCUSDT non-negative with PF >= 1.05 if BTC-relevant, acceptable basket breadth, no excessive concentration, and evidence that the regime filter improves expectancy rather than merely reducing trades.

Fail conditions include negative aggregate holdout PnL, PF < 1.00, negative BTCUSDT result for BTC-relevant framing, hidden weak markets, excessive concentration, reduced trades without expectancy improvement, or changing thresholds after seeing results.

## Implementation Boundary

This definition plan does not authorize validation execution, dry-run, live trading, production changes, or implementation. Implementation readiness remains closed / not ready.
