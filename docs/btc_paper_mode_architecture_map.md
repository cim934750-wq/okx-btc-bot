# BTC Paper-Mode Architecture Map

## Purpose

This document maps the BTC Long1 paper-mode MVP from public data refresh through signal, risk, response, reporting, schema, and future safety boundaries.

It is documentation only. It does not add runtime trading code, order-intent writing, exchange adapters, testnet trading, live trading, private API calls, API keys, account reads, real position management, or external notifications.

## Architecture Diagram

```text
OKX public candles, no keys
        |
        v
scripts/refresh_btcusdt_4h_data.py
btc_signal/data_refresh.py
        |
        v
data/BTCUSDT_4h.csv  <-----------------------------+
        |                                           |
        v                                           |
scripts/run_btc_signal_once.py                      |
btc_signal/runner.py                                |
        |                                           |
        v                                           |
btc_signal/signal_engine.py                         |
Long1-only deterministic signal decision            |
        |                                           |
        v                                           |
btc_signal/risk_engine.py                           |
stale data, risk flags, paper-state checks          |
        |                                           |
        v                                           |
btc_signal/response_engine.py                       |
WAIT / WATCH / PAPER_LONG / BLOCK / EXIT_WARNING    |
        |                                           |
        +--------------------+----------------------+
                             |
                             v
                 runtime/paper_state.json
                 runtime/logs/btc_signal_decisions_*.jsonl
                             |
         +-------------------+--------------------+
         |                   |                    |
         v                   v                    v
btc_signal/monitoring.py  btc_signal/status_dashboard.py  btc_signal/daily_review.py
dry-run report            paper status dashboard           daily snapshots/comparison
         |                   |                    |
         +-------------------+--------------------+
                             |
                             v
                  btc_signal/alert_summary.py
                  INFO / WARN / BLOCKED
                             |
                             v
                  btc_signal/operator_checklist.py
                  manual paper-mode steps only

schemas/btc_order_intent.schema.json
        |
        v
btc_signal/order_intent_schema_audit.py
scripts/audit_btc_order_intent_schema.py
read-only schema safety audit

Future boundaries, not implemented:
        |
        +--> OrderIntentWriter -> runtime/order_intents/*.json, non-executing only
        +--> SimulatedDryRunAdapter -> local simulated fills only
        +--> TestnetAdapter -> future, approval-gated only
        +--> RestrictedLiveAdapter -> forbidden
```

## Component Table

| Component | File/module path | Purpose | Inputs | Outputs | Writes state/logs? | Requires API key? | Can trade? | Safety boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Public data refresh | `scripts/refresh_btcusdt_4h_data.py`, `btc_signal/data_refresh.py` | Fetch and normalize recent BTCUSDT 4h candles from public OKX market data. | OKX public candles, existing local CSV. | `data/BTCUSDT_4h.csv`, refresh report. | Yes: CSV and `runtime/data_refresh_reports/*.json`. | No. | No. | Public market data only; no account endpoint. |
| Local CSV data | `data/BTCUSDT_4h.csv` | Local OHLCV source for paper signal evaluation. | Public refresh output or checked-in BTC fixture data. | Data frame loaded by signal flow. | No active code. | No. | No. | Must preserve `timestamp,open,high,low,close,volume`. |
| Feature builder | `btc_signal/features.py`, `research/indicators.py` | Build deterministic research feature frame. | BTCUSDT 4h OHLCV data. | Feature frame. | No. | No. | No. | Deterministic feature computation only. |
| Signal engine | `btc_signal/signal_engine.py` | Evaluate Long1-only signal on the latest completed candle. | Feature frame, `BtcSignalConfig`. | `SignalDecision`. | No. | No. | No. | Ignores shorts and Long2; no AI inference. |
| Risk engine | `btc_signal/risk_engine.py` | Detect stale data, missing features, NaNs, ATR problems, extreme distance, regime mismatch, cooldown, duplicate paper position, and drawdown guard. | Signal decision, feature frame, config, optional paper state. | `RiskAssessment`. | No. | No. | No. | Fails closed to `BLOCK` for stale/missing/invalid conditions. |
| Response engine | `btc_signal/response_engine.py` | Combine signal and risk into safe paper action. | `SignalDecision`, `RiskAssessment`, optional paper state. | `ResponseDecision`. | No. | No. | No. | Allowed actions only: `WAIT`, `WATCH`, `PAPER_LONG`, `BLOCK`, `EXIT_WARNING`. |
| Paper state | `btc_signal/paper_state.py` | Store local paper position state. | Response result, current price, prior paper state. | `runtime/paper_state.json`. | Yes: local paper state only. | No. | No real trade. | Local JSON only; no exchange position. |
| Decision logs | `btc_signal/reporting.py`, `btc_signal/runner.py` | Append inspectable signal/risk/response decisions. | Current run result. | `runtime/logs/btc_signal_decisions_*.jsonl`. | Yes: local JSONL logs. | No. | No. | Audit/log output only. |
| Paper loop | `scripts/run_btc_paper_loop.py` | Optional local dry-run loop. | Local CSV and paper state. | Same paper decision outputs as one-shot run. | Yes: paper logs/state as applicable. | No. | No. | Defaults to once-per-run unless interval is explicit. |
| Monitoring report | `btc_signal/monitoring.py`, `scripts/report_btc_dry_run_status.py` | Summarize recent decision logs and paper state. | JSONL logs, paper state. | Text/JSON/Markdown report. | Optional explicit report output only. | No. | No. | Read-only by default. |
| Paper status dashboard | `btc_signal/status_dashboard.py`, `scripts/report_btc_paper_status.py` | Combine data freshness, latest signal, risk/response, monitoring, and paper state. | CSV, logs, paper state. | Text/JSON/Markdown status view. | Optional explicit report output only. | No. | No. | Read-only by default; does not refresh data unless separately commanded. |
| Daily review | `btc_signal/daily_review.py`, `scripts/review_btc_daily_dry_run.py` | Archive compact status snapshot and compare with prior snapshot. | Dashboard inputs, prior snapshot. | `runtime/daily_reviews/*.json` and optional Markdown. | Yes: local daily review snapshots/reports. | No. | No. | Review artifacts only; no trading action. |
| Alert summary | `btc_signal/alert_summary.py`, `scripts/summarize_btc_daily_alerts.py` | Classify daily review as `INFO`, `WARN`, or `BLOCKED`. | Daily review snapshot/report. | Text/JSON/Markdown alert summary. | Optional explicit report output only. | No. | No. | Local read-only classification; no notifications. |
| Operator checklist | `btc_signal/operator_checklist.py`, `scripts/print_btc_operator_checklist.py` | Print manual steps for alert states. | Alert summary, daily review. | Text/JSON/Markdown checklist. | Optional explicit checklist output only. | No. | No. | Does not execute remediation. |
| Order-intent schema | `schemas/btc_order_intent.schema.json` | Validate future non-executing intent record shape. | Candidate JSON object in tests/future designs. | Validation pass/fail. | No. | No. | No. | Requires `execution_allowed=false`; rejects `testnet`, `live`, and credential-like fields. |
| Schema audit | `btc_signal/order_intent_schema_audit.py`, `scripts/audit_btc_order_intent_schema.py` | Read schema and print safety constraints. | `schemas/btc_order_intent.schema.json`. | Text/JSON/Markdown audit. | Optional explicit audit output only. | No. | No. | Read-only; does not write intents. |
| Future OrderIntentWriter | Not implemented. Design: `docs/btc_order_intent_design.md`. | Future append-only non-executing intent writer. | Future approved local decisions/reports only. | Future `runtime/order_intents/*.json`. | Future local runtime files only. | No. | No. | May be considered next, but non-executing only. |
| Future simulated dry-run adapter | Not implemented. Design: `docs/btc_exchange_adapter_boundaries.md`. | Future local simulated fills from local data. | Future validated intents and local OHLCV. | Future simulation audit reports. | Future local reports only. | No. | No real trade. | Local simulation only. |
| Future testnet adapter | Not implemented. Design: `docs/btc_testnet_transition_plan.md`. | Future testnet lifecycle only after explicit approval. | Future approved testnet config and safety gates. | Future testnet audit reports. | Future approval-gated. | Future testnet keys only. | Testnet only after approval. | Not available now. |
| Forbidden live adapter | Not implemented. Design: `docs/btc_exchange_adapter_boundaries.md`. | Explicitly forbidden live boundary. | None. | None. | No. | Live keys forbidden. | No. | Live remains forbidden. |

## Command Map

| Command | Component used | Read/write behavior | Expected runtime output | Safety status |
| --- | --- | --- | --- | --- |
| `python scripts/refresh_btcusdt_4h_data.py` | Public data refresh | Reads public OKX candles and existing CSV; writes local CSV/report. | `data/BTCUSDT_4h.csv`, `runtime/data_refresh_reports/*.json`. | Public-data only, no keys, no trading. |
| `python scripts/run_btc_signal_once.py` | Runner, signal, risk, response, paper state, reporting | Reads CSV/state; writes decision log and paper state if paper action occurs. | `runtime/logs/btc_signal_decisions_*.jsonl`, `runtime/paper_state.json`. | Paper-only; no exchange call. |
| `python scripts/run_btc_paper_loop.py` | Paper loop runner | Reads CSV/state; writes same paper outputs as one-shot when run. | Decision logs and paper state as applicable. | Paper-only; defaults safely. |
| `python scripts/report_btc_dry_run_status.py` | Monitoring report | Reads logs/state; writes only explicit output paths. | Optional `runtime/reports/*.json` or `*.md`. | Read-only by default. |
| `python scripts/report_btc_paper_status.py` | Status dashboard | Reads CSV/logs/state; writes only explicit output paths. | Optional `runtime/reports/*.json` or `*.md`. | Read-only by default. |
| `python scripts/review_btc_daily_dry_run.py` | Daily review | Reads dashboard inputs and prior snapshot; writes review snapshots. | `runtime/daily_reviews/*.json` or `*.md`. | Review-only; no trading. |
| `python scripts/summarize_btc_daily_alerts.py` | Alert summary | Reads daily review; writes only explicit output paths. | Optional `runtime/daily_reviews/*alert*.json` or `*.md`. | Read-only; no notifications. |
| `python scripts/print_btc_operator_checklist.py` | Operator checklist | Reads alert/review; writes only explicit output paths. | Optional `runtime/daily_reviews/*checklist*.json` or `*.md`. | Prints manual steps only. |
| `python scripts/audit_btc_order_intent_schema.py` | Schema audit | Reads schema; writes only explicit output paths. | Optional `runtime/reports/*schema_audit*.json` or `*.md`. | Read-only schema safety check. |

## Data And Artifact Flow

- `data/BTCUSDT_4h.csv`: local paper-mode BTCUSDT 4h OHLCV source. It is refreshed from public OKX candles and consumed by the signal/status paths.
- `runtime/paper_state.json`: local paper position state. It is not an exchange position and must not be treated as real account state.
- `runtime/logs/btc_signal_decisions_*.jsonl`: append-only local decision logs for signal, risk, response, and paper state context.
- `runtime/data_refresh_reports/*.json`: public-data refresh provenance reports.
- `runtime/reports/*.json` or `runtime/reports/*.md`: optional status, monitoring, and schema audit reports when explicit output paths are provided.
- `runtime/daily_reviews/*.json` or `runtime/daily_reviews/*.md`: daily review snapshots, alert summaries, and checklist outputs when generated.
- `schemas/btc_order_intent.schema.json`: non-executing order-intent schema. It is a validation artifact, not a writer or adapter.

Runtime artifacts are local inspection outputs. They should not be committed unless intentionally added as small fixtures.

## Safety Gates

- Stale data gate: stale latest candle or stale-data risk flag blocks paper action and future intent execution.
- Incomplete candle gate: refresh excludes incomplete latest public candles where possible; future action must use completed candles only.
- Long1 condition gate: signal engine requires the deterministic Long1 condition set; shorts and Long2 are out of scope.
- Risk flag gate: unresolved risk flags block or downgrade response based on risk level; `BLOCK` risk fails closed.
- Response action gate: response is limited to `WAIT`, `WATCH`, `PAPER_LONG`, `BLOCK`, and `EXIT_WARNING`.
- Paper state consistency gate: duplicate open paper position, malformed state, or drawdown guard prevents new paper entries.
- Order-intent schema gate: future intent records must validate against `schemas/btc_order_intent.schema.json`.
- Schema audit gate: `scripts/audit_btc_order_intent_schema.py` must report `PASS` before any future writer is considered.
- Operator checklist gate: alert/checklist review remains a manual paper-mode checkpoint and must not be bypassed.

## Forbidden Capabilities

- Live orders.
- Exchange order placement.
- Private API calls.
- API keys.
- Account reads.
- Real position management.
- External notifications.
- Hidden auto-execution.
- Production deployment.
- Strategy threshold optimization for profitability claims.
- Testnet or live readiness claims.

## Future Boundaries

- `OrderIntentWriter` may be considered next only as a non-executing append-only writer to `runtime/order_intents/*.json`.
- Future order intents must keep `execution_allowed=false` until a separately approved design changes that boundary.
- Exchange adapters remain future-only and must not be introduced as part of paper reporting.
- `SimulatedDryRunAdapter` remains future-only and may simulate local fills only from local data after separate approval.
- `TestnetAdapter` remains approval-gated and must require kill-switch, schema, audit, and API-key safety reviews.
- `RestrictedLiveAdapter` remains forbidden.

## Recommended Next Engineering Choices

- Option A: stop here and run multi-day paper observation using the command index.
- Option B: add a non-executing `OrderIntentWriter` that writes only validated local JSON to `runtime/order_intents/*.json`.
- Option C: add simulated dry-run adapter design only, without implementation.
- Option D: improve documentation and tests only, keeping runtime behavior unchanged.

The safest next implementation step, if any implementation is requested later, is Option B with `execution_allowed=false`, no exchange adapter, no API keys, and no order placement.
