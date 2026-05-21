# Candidate D Later-Data Validation Round 1

## Scope

This is a research-only later-data validation attempt for Candidate D. It did not restart dry-run, enable live trading, modify deployment/systemd/live-loop behavior, modify PR #1/#2/#3, change production source code, change production parameters, optimize, sweep thresholds, tune Candidate D values, remove DOGE/DOT/UNI, fetch OHLCV, synthesize OHLCV, or claim implementation readiness.

## Frozen Candidate D Rules

- Timeframe: 4h.
- Long entry: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, and close > previous close.
- Stop: recent 10-candle low - 0.5 * ATR14.
- Exit: EMA20 touch, 1.5R take profit, or time stop after 8 completed 4h candles.
- No averaging down.
- No add-on entries.
- No parameter changes.

## Data Availability Finding

The repository was inspected for local later/new 4h OHLCV before running any validation. The only local 4h OHLCV files found were the same 19 `data/*USDT_4h.csv` market files used by prior batch/confirmation validations: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. `BTCUSDT_1h.csv` exists but remains excluded.

The local 4h file coverage spans from 2019-01-01T00:00:00+00:00 to latest observed market timestamp 2026-05-16T16:00:00+00:00, with varying per-market end dates documented in the data coverage CSV. However, there is no separate, verifiable later-only OHLCV dataset or appended segment that can be proven to be strictly after the prior batch/confirmation validation period. The prior confirmation note states that the existing local 4h data was already used for the confirmation cycle and that no new OHLCV was fetched.

## Decision

Decision: `data_unavailable_stop_no_validation`. Per the approved priority order, no new OHLCV was fetched, no missing data was inferred, and Candidate D later-data validation was not executed.

## Interpretation

Candidate D remains research-confirmed from the prior confirmation validation, but it is not later-data validated and remains not implementation-ready. No dry-run, live trading, production implementation, or parameter change is authorized.
