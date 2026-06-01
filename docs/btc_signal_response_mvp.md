# BTC Signal Response MVP

## Purpose

This MVP turns the current BTC-focused Long1-only research candidate into a deterministic paper/dry-run signal automation framework. It is built for inspection, logging, and future validation, not for live trading.

For the operator-facing command sequence, see the [BTC Paper-Mode Command Index](btc_paper_mode_command_index.md).

For the component-level paper-mode system map, see the [BTC Paper-Mode Architecture Map](btc_paper_mode_architecture_map.md).

Design-only future transition documents:

- [BTC Order Intent Design](btc_order_intent_design.md)
- [BTC Exchange Adapter Boundary Design](btc_exchange_adapter_boundaries.md)
- [BTC Kill Switch And Safety Gate Design](btc_kill_switch_and_safety_gates.md)
- [BTC Testnet Transition Plan](btc_testnet_transition_plan.md)

## What The System Does

- Loads BTCUSDT 4h OHLCV data from `data/BTCUSDT_4h.csv`.
- Can refresh local BTCUSDT 4h paper data from OKX public market candles without API keys.
- Builds the existing research feature frame through `research.indicators.build_feature_frame`.
- Evaluates the latest completed 4h candle for the Long1 starter signal.
- Emits a structured signal decision with the passed and missing variables.
- Runs variable and risk checks before any response is selected.
- Records local paper state and JSONL logs under `runtime/`.
- Generates read-only monitoring reports from local decision logs and paper state.
- Generates a read-only paper status dashboard that combines data freshness, latest signal/risk/response, monitoring counts, and paper state.
- Archives read-only daily dry-run review snapshots and compares the current snapshot with the prior snapshot.
- Summarizes daily review alerts locally as `INFO`, `WARN`, or `BLOCKED` without sending external notifications.
- Prints a read-only operator checklist for `INFO`, `WARN`, and `BLOCKED` paper-mode alert states.
- Supports a one-shot run and a local optional dry-run loop.

## What It Does Not Do

- It does not connect to authenticated OKX or any private exchange/account endpoint.
- It does not require API keys.
- It does not place live orders.
- It does not evaluate shorts or Long2 add-on entries.
- It does not optimize parameters, sweep thresholds, or claim profitability.
- It does not make the strategy implementation-ready for live trading.
- The monitoring report is read-only; it does not refresh data, place orders, or mutate paper state.
- The paper status dashboard is read-only by default and does not refresh data or mutate paper state.
- The daily dry-run review is read-only by default; it archives local status snapshots and does not refresh data or mutate paper state.
- The alert summary is local and read-only; it does not send email, chat, webhook, SMS, push, or any other external notification.
- The operator checklist prints manual steps only; it does not execute remediation, refresh data, run signals, send notifications, or trade.
- The order-intent, adapter, kill-switch, and testnet documents are design-only; they do not add private API access, exchange orders, or live trading.
- The order-intent JSON schema validates non-executing record shape only; it does not create intents, connect to an exchange, or trade.
- The order-intent schema audit command reads the schema and prints safety constraints only; it does not write intents, add adapters, call APIs, or trade.
- The OrderIntentWriter design review checklist prints future implementation gates only; it does not write `runtime/order_intents/`, add a writer, add adapters, call APIs, or trade.
- The architecture map is documentation only; it links current paper components and future boundaries without adding trading code.

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

## How To Run The Paper Loop

Run once through the dry-run loop entry point:

```bash
.venv-btc-signal-mvp/bin/python scripts/run_btc_paper_loop.py
```

Add `--interval-seconds N` only for an explicit local loop interval. This remains paper-only and does not require API keys.

## How To Generate A Monitoring Report

```bash
.venv-btc-signal-mvp/bin/python scripts/report_btc_dry_run_status.py --limit 20
```

The monitoring report reads local JSONL decision logs and `runtime/paper_state.json`. It does not call OKX, does not refresh market data, does not require API keys, and does not mutate paper state. Useful options:

```bash
.venv-btc-signal-mvp/bin/python scripts/report_btc_dry_run_status.py --format json
.venv-btc-signal-mvp/bin/python scripts/report_btc_dry_run_status.py --logs-dir runtime/logs --state-path runtime/paper_state.json
.venv-btc-signal-mvp/bin/python scripts/report_btc_dry_run_status.py --output-json runtime/reports/btc_dry_run_status.json --output-md runtime/reports/btc_dry_run_status.md
```

The report summarizes:

- total valid log entries read and recent entries summarized,
- first/latest decision `run_at` timestamps,
- latest candle timestamp from the signal log,
- stale-data flag count,
- signal decision, response action, and risk level counts,
- top risk flags,
- Long1 active, `PAPER_LONG`, `BLOCK`, `WATCH`, and `EXIT_WARNING` counts,
- latest decision summary,
- paper position state,
- inferred paper-state changes across the summarized logs,
- warnings for missing logs, missing state, malformed JSONL, stale logs, or stale-data risk flags.

## How To Generate The Paper Status Dashboard

```bash
.venv-btc-signal-mvp/bin/python scripts/report_btc_paper_status.py --limit 20
```

The status dashboard is a single read-only view over local paper-mode files. It does not call private APIs, does not place orders, does not open or close positions, and does not refresh market data by default. Refresh market data separately with `scripts/refresh_btcusdt_4h_data.py` when needed.

Useful options:

```bash
.venv-btc-signal-mvp/bin/python scripts/report_btc_paper_status.py --format json
.venv-btc-signal-mvp/bin/python scripts/report_btc_paper_status.py --data-path data/BTCUSDT_4h.csv --logs-dir runtime/logs --state-path runtime/paper_state.json
.venv-btc-signal-mvp/bin/python scripts/report_btc_paper_status.py --output-json runtime/reports/btc_paper_status.json --output-md runtime/reports/btc_paper_status.md
```

The dashboard combines:

- BTCUSDT 4h CSV path, row count, latest candle timestamp, candle age, and stale/not-stale status,
- latest deterministic Long1 signal decision, confidence, evidence, passed condition count, and missing condition count,
- latest risk level, risk flags, and response action,
- current paper position state,
- recent monitoring counts for signal decisions, response actions, risk levels, stale-data flags, and top risk flags,
- warnings for stale data, missing logs, missing state, invalid CSV, or evaluation failures.

All dashboard outputs are paper/dry-run status summaries. They do not enable live trading and do not claim profitability.

## How To Run The Daily Dry-Run Review

```bash
.venv-btc-signal-mvp/bin/python scripts/review_btc_daily_dry_run.py --limit 20
```

The daily review command builds a compact snapshot from the paper status dashboard, writes it under `runtime/daily_reviews/`, and compares it with the prior `btc_daily_review_latest.json` snapshot if one exists. It is read-only with respect to trading and market data: it does not call private APIs, does not place orders, does not open or close positions, and does not refresh BTC data by default.

Useful options:

```bash
.venv-btc-signal-mvp/bin/python scripts/review_btc_daily_dry_run.py --format json
.venv-btc-signal-mvp/bin/python scripts/review_btc_daily_dry_run.py --compare-to runtime/daily_reviews/btc_daily_review_latest.json
.venv-btc-signal-mvp/bin/python scripts/review_btc_daily_dry_run.py --output-json runtime/daily_reviews/btc_daily_review_report.json --output-md runtime/daily_reviews/btc_daily_review_report.md
```

Each snapshot includes:

- BTCUSDT 4h data path, row count, latest candle timestamp, candle age, and stale status,
- latest signal decision, Long1 active status, confidence, passed/missing condition counts, and main missing conditions,
- latest risk level, risk flags, and response action,
- paper position open/closed state, side, entry time, and entry price,
- monitoring counts for total entries, summarized entries, signal decisions, response actions, risk levels, stale-data flags, and top risk flags,
- warnings.

The comparison flags changed latest candle timestamp, stale status, signal decision, Long1 active status, confidence, condition counts, new/resolved missing conditions, risk level, new/resolved risk flags, response action, paper position open/closed state, side, monitoring log count, stale-data count, and warning count.

## How To Run The Daily Alert Summary

Run the daily review first so the latest snapshot/report exists:

```bash
.venv-btc-signal-mvp/bin/python scripts/review_btc_daily_dry_run.py --limit 20
```

Then summarize alert severity locally:

```bash
.venv-btc-signal-mvp/bin/python scripts/summarize_btc_daily_alerts.py
```

Useful options:

```bash
.venv-btc-signal-mvp/bin/python scripts/summarize_btc_daily_alerts.py --format json
.venv-btc-signal-mvp/bin/python scripts/summarize_btc_daily_alerts.py --review-json runtime/daily_reviews/btc_daily_review_report_latest.json
.venv-btc-signal-mvp/bin/python scripts/summarize_btc_daily_alerts.py --snapshot-json runtime/daily_reviews/btc_daily_review_latest.json --compare-to runtime/daily_reviews/btc_daily_review_YYYYMMDDTHHMMSSZ.json
.venv-btc-signal-mvp/bin/python scripts/summarize_btc_daily_alerts.py --output-json runtime/daily_reviews/btc_daily_alert_summary_latest.json --output-md runtime/daily_reviews/btc_daily_alert_summary_latest.md
```

Severity meanings:

- `INFO`: data is fresh, signal remains `WAIT`/`WATCH` without blocking risk, paper state is closed/unchanged, and no new risk flags or stale warnings appeared.
- `WARN`: signal/confidence changed, Long1 is active without `PAPER_LONG`, new non-blocking risk flags appeared, candle age is near stale, monitoring log count did not advance, or warnings increased.
- `BLOCKED`: stale data is active, response is `BLOCK`, risk level is `BLOCK`, required data/log/state is missing, paper state is inconsistent, or input parsing failed.

The alert summary only classifies local review state for human inspection. It does not send external notifications, does not refresh data by default, does not place orders, and does not enable live trading.

## How To Run The Operator Checklist

Run the alert summary first so the latest alert JSON exists:

```bash
.venv-btc-signal-mvp/bin/python scripts/summarize_btc_daily_alerts.py --output-json runtime/daily_reviews/btc_daily_alert_summary_latest.json
```

Then print the checklist:

```bash
.venv-btc-signal-mvp/bin/python scripts/print_btc_operator_checklist.py
```

Useful options:

```bash
.venv-btc-signal-mvp/bin/python scripts/print_btc_operator_checklist.py --format json
.venv-btc-signal-mvp/bin/python scripts/print_btc_operator_checklist.py --alert-json runtime/daily_reviews/btc_daily_alert_summary_latest.json
.venv-btc-signal-mvp/bin/python scripts/print_btc_operator_checklist.py --review-json runtime/daily_reviews/btc_daily_review_report_latest.json
.venv-btc-signal-mvp/bin/python scripts/print_btc_operator_checklist.py --output-json runtime/daily_reviews/btc_operator_checklist_latest.json --output-md runtime/daily_reviews/btc_operator_checklist_latest.md
```

Recommended manual command order for a `BLOCKED` stale-data state:

```bash
python scripts/refresh_btcusdt_4h_data.py
python scripts/run_btc_signal_once.py
python scripts/report_btc_paper_status.py
python scripts/review_btc_daily_dry_run.py
python scripts/summarize_btc_daily_alerts.py
python scripts/print_btc_operator_checklist.py
```

Severity-specific checklist behavior:

- `INFO`: confirm data freshness, signal/risk/response, and paper state; archive a daily review; keep observing; take no trading action.
- `WARN`: inspect changed fields and new/resolved risk flags; rerun the paper status dashboard and daily review; refresh public data only if stale or near-stale; do not change thresholds; do not promote to live trading.
- `BLOCKED`: identify blocked reason; refresh public BTC data manually if `stale_data` is active; rerun the paper signal, status dashboard, daily review, and alert summary; inspect risk flags; do not override `BLOCK`; do not create a paper or live entry; do not infer missing data.

The checklist is a read-only operator aid. It prints exact manual steps and safety boundaries, but it does not run the steps for you and does not implement live trading.

## How To Run Tests

```bash
.venv-btc-signal-mvp/bin/python -m py_compile btc_signal/*.py scripts/run_btc_signal_once.py scripts/run_btc_paper_loop.py scripts/refresh_btcusdt_4h_data.py scripts/report_btc_dry_run_status.py scripts/report_btc_paper_status.py scripts/review_btc_daily_dry_run.py scripts/summarize_btc_daily_alerts.py scripts/print_btc_operator_checklist.py scripts/audit_btc_order_intent_schema.py scripts/review_btc_order_intent_writer_design.py
.venv-btc-signal-mvp/bin/python -m compileall research btc_signal scripts
.venv-btc-signal-mvp/bin/python -m pytest tests/test_btc_signal_engine.py tests/test_btc_risk_engine.py tests/test_btc_response_engine.py tests/test_btc_data_refresh.py tests/test_btc_monitoring.py tests/test_btc_status_dashboard.py tests/test_btc_daily_review.py tests/test_btc_alert_summary.py tests/test_btc_operator_checklist.py tests/test_btc_order_intent_schema.py tests/test_btc_order_intent_schema_audit.py tests/test_btc_order_intent_writer_review.py
```

## Why Live Trading Is Blocked

The Long1-only candidate remains research-only and concentrated. This MVP exists to make signal generation observable and to collect dry-run behavior safely. Live trading requires a separate explicit user approval step and additional validation.

## Next Steps Before Any Real Trading

1. Holdout/new-data validation.
2. Longer dry-run.
3. Logging review.
4. Risk checks.
5. Explicit user approval.

Design-only architecture references for a possible future testnet discussion:

1. [BTC Order Intent Design](btc_order_intent_design.md).
2. [BTC Exchange Adapter Boundary Design](btc_exchange_adapter_boundaries.md).
3. [BTC Kill Switch And Safety Gate Design](btc_kill_switch_and_safety_gates.md).
4. [BTC Testnet Transition Plan](btc_testnet_transition_plan.md).
5. [BTC Paper-Mode Architecture Map](btc_paper_mode_architecture_map.md).

The non-executing order-intent schema is available at `schemas/btc_order_intent.schema.json`. It requires `execution_allowed=false` and rejects `testnet`, `live`, unknown fields, and credential-like fields.
