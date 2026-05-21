# Candidate D Mean-Reversion Confirmation Validation Round 1

## Scope

This is a research-only standalone confirmation validation for Candidate D. It does not restart dry-run, enable live trading, modify production source code, modify production parameters, modify deployment/systemd/live-loop behavior, fetch OHLCV, optimize, sweep thresholds, or claim implementation readiness.

## Frozen Candidate D Rules

- Timeframe: 4h.
- Long entry: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, and close > previous close.
- Stop: recent 10-candle low - 0.5 * ATR14.
- Exit: EMA20 touch, 1.5R take profit, or time stop after 8 completed 4h candles.
- No averaging down and no add-on entries.

## Data Scope

The validation used the same 19 local 4h markets and chronological 70/30 split used in prior validations. BTCUSDT_1h.csv was excluded. BTCUSDT, DOGE, DOT, and UNI remained visible. No new/fake/inferred OHLCV was used.

## Result

Holdout net PnL was 3853.32, PF 1.7601, with 339 trades, win rate 55.46%, average trade 11.37, median trade 12.13, and positive markets 18/19. BTCUSDT was 253.84 with PF 2.3689. Batch reproduction was consistent for key metrics.

## Decision

Decision: `pass_research_confirmation_requires_no_trading_action`. This is research confirmation only. It does not authorize dry-run, live trading, production implementation, or parameter changes.
