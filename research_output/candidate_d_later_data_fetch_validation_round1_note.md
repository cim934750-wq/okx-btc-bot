# Candidate D Later-Data Fetch Validation Round 1

## Scope

Research-only later-data validation after explicit approval to fetch later 4h OHLCV for the same 19 markets. This run did not restart dry-run, enable live trading, modify deployment/systemd/live-loop behavior, modify PR #1/#2/#3, change production strategy source, change production parameters, optimize, sweep thresholds, tune Candidate D values, remove DOGE/DOT/UNI, select markets after results, or claim implementation readiness.

## Data Source

Source: okx_public_ohlcv_via_ccxt. Fetch time: 2026-05-21T08:49:51.190984+00:00. Fetched 4h candles only for the approved 19 markets. `BTCUSDT_1h.csv` was excluded. Existing historical files were preserved; fetched later rows were saved separately to `research_output/candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv`. The coverage audit documents a one-candle initial source gap per market from the requested start; no missing candle was filled or inferred.

## Frozen Candidate D Rules

- Timeframe: 4h.
- Long entry: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, and close > previous close.
- Stop: recent 10-candle low - 0.5 * ATR14.
- Exit: EMA20 touch, 1.5R take profit, or time stop after 8 completed 4h candles.
- No averaging down.
- No add-on entries.
- No parameter changes.

## Later-Data Result

Later-data aggregate net PnL was -174.23, PF 0.13132609206323043, across 15 trades. BTCUSDT net PnL was -11.62 across 1 trades. Positive markets: 2; negative markets: 9; flat/no-trade markets: 8.

## Decision

Decision: `fail`. This remains research-only and does not authorize implementation, dry-run, live trading, or parameter changes.
