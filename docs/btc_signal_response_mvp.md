# BTC Signal Response MVP

## Purpose

This MVP turns the current BTC-focused Long1-only research candidate into a deterministic paper/dry-run signal automation framework. It is built for inspection, logging, and future validation, not for live trading.

## What The System Does

- Loads BTCUSDT 4h OHLCV data from `data/BTCUSDT_4h.csv`.
- Can refresh local BTCUSDT 4h paper data from OKX public market candles without API keys.
- Builds the existing research feature frame through `research.indicators.build_feature_frame`.
- Evaluates the latest completed 4h candle for the Long1 starter signal.
- Emits a structured signal decision with the passed and missing variables.
- Runs variable and risk checks before any response is selected.
- Records local paper state and JSONL logs under `runtime/`.
- Supports a one-shot run and a local optional dry-run loop.

## What It Does Not Do

- It does not connect to authenticated OKX or any private exchange/account endpoint.
- It does not require API keys.
- It does not place live orders.
- It does not evaluate shorts or Long2 add-on entries.
- It does not optimize parameters, sweep thresholds, or claim profitability.
- It does not make the strategy implementation-ready for live trading.

## Signal Logic

The signal model uses default `research.config.StrategyParams` and checks the existing Long1 starter signal only:

- `weekly_bull`
- `daily_bull`
- `exec_bull_structure`
- `exec_slope_up`
- `exec_adx_pass`
- `exec_atr_pass`
- `exec_distance_pass`
- `exec_bull_momentum`
- `long_pullback`
- `long_resumption`

If `starter_long_signal` is true, the engine returns `LONG_SIGNAL` with `signal_name = Long1`. If the signal is not complete but most conditions pass, it returns `WATCH`. Otherwise it returns `WAIT`. Missing or invalid features return `BLOCKED`.

## Variable And Risk Response Logic

`risk_engine.py` checks:

- stale data,
- missing feature columns,
- NaN latest features,
- invalid or unusually low ATR,
- extreme distance from EMA50,
- weekly/daily regime mismatch,
- sudden volatility expansion,
- recent paper signal cooldown,
- duplicate open paper position,
- paper drawdown guard.

Risk levels are `LOW`, `MEDIUM`, `HIGH`, and `BLOCK`. Stale, missing, NaN, invalid ATR, signal-blocked, and drawdown-guard conditions block automation.

## Paper/Dry-Run Boundary

Responses are limited to:

- `WAIT`
- `WATCH`
- `PAPER_LONG`
- `BLOCK`
- `EXIT_WARNING`

There is no `LIVE_BUY` path. A `PAPER_LONG` only updates `runtime/paper_state.json` and writes a log entry. No exchange client, credentials, or order endpoint is used.

## How To Refresh BTCUSDT 4h Paper Data

```bash
.venv-btc-signal-mvp/bin/python scripts/refresh_btcusdt_4h_data.py
```

The refresh script uses OKX public market candles for `BTC-USDT` with bar `4H`. It requires no API keys, account access, or exchange credentials. By default it:

- fetches recent public candles,
- excludes exchange-reported incomplete candles,
- validates the CSV schema,
- deduplicates timestamps,
- sorts candles ascending,
- writes `data/BTCUSDT_4h.csv`,
- writes a JSON provenance report under `runtime/data_refresh_reports/`.

The expected CSV schema stays:

```text
timestamp,open,high,low,close,volume
```

This refresh path only updates local paper-mode market data. It does not enable live trading, exchange orders, account data, or position management.

## How To Run Once

```bash
.venv-btc-signal-mvp/bin/python scripts/run_btc_signal_once.py
```

Run the refresh first if the local CSV is stale, then run the signal demo. The signal script prints a JSON result and appends a JSONL decision record under `runtime/logs/`.

## How To Run Tests

```bash
.venv-btc-signal-mvp/bin/python -m py_compile btc_signal/*.py scripts/run_btc_signal_once.py scripts/run_btc_paper_loop.py
.venv-btc-signal-mvp/bin/python -m compileall research btc_signal scripts
.venv-btc-signal-mvp/bin/python -m pytest tests/test_btc_signal_engine.py tests/test_btc_risk_engine.py tests/test_btc_response_engine.py tests/test_btc_data_refresh.py
```

## Why Live Trading Is Blocked

The Long1-only candidate remains research-only and concentrated. This MVP exists to make signal generation observable and to collect dry-run behavior safely. Live trading requires a separate explicit user approval step and additional validation.

## Next Steps Before Any Real Trading

1. Holdout/new-data validation.
2. Longer dry-run.
3. Logging review.
4. Risk checks.
5. Explicit user approval.
