# BTC Paper-Mode Command Index

## Purpose

This document is the operator-facing command index for the BTC Long1 paper-mode MVP. It lists the safe manual workflow from public BTCUSDT 4h data refresh through alert checklist review.

The workflow is deterministic, local, and inspectable. It does not enable live trading.

## Safety Boundary

- Paper mode only.
- No private API keys.
- No account data.
- No exchange order placement.
- No real position management.
- No external notifications.
- No production deployment.
- No profitability or live-trading readiness claims.
- Do not override `BLOCK`, `WARN`, stale-data, malformed-input, or risk flags manually.

## Full Safe Workflow Order

Run these commands from the repository root:

```bash
python scripts/refresh_btcusdt_4h_data.py
python scripts/run_btc_signal_once.py
python scripts/report_btc_paper_status.py
python scripts/report_btc_dry_run_status.py
python scripts/review_btc_daily_dry_run.py
python scripts/summarize_btc_daily_alerts.py
python scripts/print_btc_operator_checklist.py
```

## Command Reference

### 1. Refresh Public BTCUSDT 4h Data

```bash
python scripts/refresh_btcusdt_4h_data.py
```

- Purpose: fetch recent BTCUSDT 4h OHLCV candles from OKX public market data and update the local paper CSV.
- Inputs: OKX public market candles endpoint, existing `data/BTCUSDT_4h.csv` when present.
- Outputs: refreshed `data/BTCUSDT_4h.csv` with schema `timestamp,open,high,low,close,volume`.
- Runtime files: JSON provenance report under `runtime/data_refresh_reports/`.
- Writes state/logs/reports: writes market data and a provenance report only.
- Requires API keys: no.
- Can trade: no.

### 2. Run One Signal Check

```bash
python scripts/run_btc_signal_once.py
```

- Purpose: evaluate the latest completed BTCUSDT 4h candle through the deterministic Long1-only signal engine, risk engine, response engine, and paper-state boundary.
- Inputs: `data/BTCUSDT_4h.csv`, local paper state when present.
- Outputs: terminal JSON with signal, risk, response, and paper-state summary.
- Runtime files: appends a JSONL decision record under `runtime/logs/`; may update `runtime/paper_state.json` only for paper actions.
- Writes state/logs/reports: writes a decision log and paper state only.
- Requires API keys: no.
- Can trade: no.

### 3. Inspect Paper Status Dashboard

```bash
python scripts/report_btc_paper_status.py
```

- Purpose: show one read-only paper-mode status view combining data freshness, latest signal evidence, risk flags, response action, monitoring summary, and paper state.
- Inputs: `data/BTCUSDT_4h.csv`, local decision logs, local paper state.
- Outputs: human-readable text by default; optional JSON or Markdown when requested.
- Runtime files: optional report files only when `--output-json` or `--output-md` is provided.
- Writes state/logs/reports: read-only by default; writes only explicit report output paths.
- Requires API keys: no.
- Can trade: no.

### 4. Generate Monitoring Report

```bash
python scripts/report_btc_dry_run_status.py
```

- Purpose: summarize the last N local decision log entries, stale-data flags, risk flags, response actions, and paper-state changes.
- Inputs: JSONL decision logs under `runtime/logs/`, `runtime/paper_state.json` when present.
- Outputs: human-readable text by default; optional JSON or Markdown when requested.
- Runtime files: optional report files only when `--output-json` or `--output-md` is provided.
- Writes state/logs/reports: read-only by default; writes only explicit report output paths.
- Requires API keys: no.
- Can trade: no.

### 5. Generate Daily Dry-Run Review

```bash
python scripts/review_btc_daily_dry_run.py
```

- Purpose: archive a compact paper-mode status snapshot and compare it with the prior snapshot.
- Inputs: paper status dashboard data, local decision logs, local paper state, previous snapshot when present.
- Outputs: human-readable review with current snapshot and prior-snapshot comparison.
- Runtime files: JSON snapshots and optional Markdown under `runtime/daily_reviews/`.
- Writes state/logs/reports: writes local review snapshots and reports only.
- Requires API keys: no.
- Can trade: no.

### 6. Summarize Daily Alerts

```bash
python scripts/summarize_btc_daily_alerts.py
```

- Purpose: classify the latest daily review state and comparison changes into `INFO`, `WARN`, or `BLOCKED`.
- Inputs: latest daily review JSON or explicit review/snapshot paths.
- Outputs: human-readable alert summary by default; optional JSON or Markdown when requested.
- Runtime files: optional alert summary files under `runtime/daily_reviews/` when output paths are provided.
- Writes state/logs/reports: read-only by default; writes only explicit alert summary output paths.
- Requires API keys: no.
- Can trade: no.

### 7. Print Operator Checklist

```bash
python scripts/print_btc_operator_checklist.py
```

- Purpose: print severity-specific manual steps for `INFO`, `WARN`, or `BLOCKED` local alert states.
- Inputs: latest alert summary JSON when present, or explicit alert/review paths.
- Outputs: human-readable checklist by default; optional JSON or Markdown when requested.
- Runtime files: optional checklist files under `runtime/daily_reviews/` when output paths are provided.
- Writes state/logs/reports: read-only by default; writes only explicit checklist output paths.
- Requires API keys: no.
- Can trade: no.

## Optional Paper Loop

```bash
python scripts/run_btc_paper_loop.py
```

The paper loop entry point defaults to a safe once-per-run dry-run mode. It remains paper-only, uses local data and local paper state, requires no API keys, and cannot place exchange orders. Use an explicit interval option only when you want a local dry-run loop.

## Severity Guide

- `INFO`: data is fresh, signal/response state is non-blocking, paper state is closed or unchanged, and no new risk flags or stale-data warnings require attention.
- `WARN`: signal evidence, confidence, risk flags, warnings, or monitoring counts changed in a way that needs human review but does not itself force a blocked state.
- `BLOCKED`: stale data, response `BLOCK`, risk level `BLOCK`, missing required local inputs, malformed input, or inconsistent paper state prevents reliable paper-mode action.

## BLOCKED Remediation

Never override `BLOCK`.

When `BLOCKED` appears:

1. Identify the blocked reason in the alert summary or checklist.
2. If `stale_data` is active, refresh public BTC data manually:

   ```bash
   python scripts/refresh_btcusdt_4h_data.py
   ```

3. Rerun one signal check:

   ```bash
   python scripts/run_btc_signal_once.py
   ```

4. Rerun the paper status dashboard:

   ```bash
   python scripts/report_btc_paper_status.py
   ```

5. Rerun the daily review:

   ```bash
   python scripts/review_btc_daily_dry_run.py
   ```

6. Rerun the alert summary:

   ```bash
   python scripts/summarize_btc_daily_alerts.py
   ```

7. Rerun the operator checklist:

   ```bash
   python scripts/print_btc_operator_checklist.py
   ```

8. Keep the system paper-only.
9. Do not change thresholds to force a signal.
10. Do not create a paper or live entry outside the existing paper response logic.

## Daily Operating Routine

- Morning or scheduled manual check: run the full safe workflow and review the alert severity.
- After each completed 4h candle if desired: refresh public data, run one signal check, then review status and alerts.
- Before reviewing any `PAPER_LONG`: run the paper status dashboard, daily review, alert summary, and operator checklist.
- After `stale_data` appears: follow the `BLOCKED` remediation sequence and do not take trading action.

## What This MVP Does Not Do

- No live trading.
- No exchange orders.
- No private API calls.
- No API keys.
- No account balance reads.
- No real position management.
- No external notifications.
- No production deployment.
- No profitability validation.
- No strategy threshold optimization.

## When To Stop

Stop manual operation and inspect the local files before continuing when:

- `stale_data` remains after public data refresh.
- Response remains `BLOCK`.
- Risk level remains `BLOCK`.
- Logs, snapshots, or paper state are malformed.
- Paper state is inconsistent with recent decision logs.
- Signal changes are unexplained by the evidence fields.
- Public data refresh reports failed fetches, invalid schema, or timestamp problems.

## Next Engineering Milestone

The next milestone should remain design-only and paper/testnet-focused:

- Order intent design only.
- Exchange adapter boundary design only.
- Kill switch design only.
- Testnet transition plan only.
- No live implementation yet.
