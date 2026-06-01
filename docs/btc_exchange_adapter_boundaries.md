# BTC Exchange Adapter Boundary Design

## Purpose

This document defines future adapter boundaries for moving from paper observation toward a possible testnet transition. It is design-only and does not implement any exchange adapter, private API call, order placement, or live trading path.

## Current Rule

The current MVP may use only paper/reporting components. It may read local market data, write paper state, write reports, and print operator guidance. It must not call private exchange endpoints or place orders.

## Adapter Classes

### PaperAdapter

- Allowed inputs: local BTCUSDT CSV data, deterministic signal decisions, risk assessments, response decisions, local paper state.
- Allowed outputs: `runtime/paper_state.json`, decision logs, paper-only status summaries.
- Forbidden operations: private API calls, testnet orders, live orders, account balance reads, order cancellation, order reconciliation against an exchange.
- Credential requirements: none.
- Order placement capability: none.
- Logging/audit requirements: JSONL decision logs and paper-state changes with timestamps and source evidence.
- Failure handling: fail closed to `BLOCK` or `WATCH`; do not infer missing data.
- Required approvals before use: already permitted inside the current paper MVP.

### OrderIntentWriter

- Allowed inputs: local signal/risk/response results, local paper state, local review snapshots, operator context.
- Allowed outputs: append-only non-executing order intent records.
- Forbidden operations: order placement, order cancellation, exchange authentication, private API calls, balance reads, position reads, mutation of real or testnet accounts.
- Credential requirements: none.
- Order placement capability: none.
- Logging/audit requirements: canonical intent record, source paths, checksum/hash, blocked reasons, `execution_allowed=false`.
- Failure handling: fail closed and write no intent when required fields are missing or malformed.
- Required approvals before use: separate explicit approval to add runtime intent writing.

### SimulatedDryRunAdapter

- Allowed inputs: validated order intent records with `execution_allowed=false`, local OHLCV data, local simulation rules, paper state.
- Allowed outputs: simulated fills, simulated rejects, simulated cancels, local simulation audit reports.
- Forbidden operations: private API calls, testnet orders, live orders, account reads, real position reconciliation.
- Credential requirements: none.
- Order placement capability: simulated local fills only.
- Logging/audit requirements: every simulated lifecycle event must reference the source intent and local candle data.
- Failure handling: fail closed when local data is stale, incomplete, missing, duplicated, or outside the simulation window.
- Required approvals before use: explicit approval after order intent schema and tests exist.

### TestnetAdapter

- Allowed inputs: future approved order intents, explicit testnet configuration, separate testnet API credentials loaded only from environment variables.
- Allowed outputs: testnet order acknowledgements, fills, cancels, rejects, timeouts, retries, reconciliation reports.
- Forbidden operations: live exchange endpoints, live credentials, withdrawal actions, production deployment, automatic promotion from paper to testnet.
- Credential requirements: future separate testnet keys only; no keys in code, config, logs, docs, or committed files.
- Order placement capability: future-only testnet orders after explicit approval.
- Logging/audit requirements: request/response metadata with secrets redacted, lifecycle events, reconciliation records, kill-switch state, operator approval records.
- Failure handling: fail closed, cancel testnet orders where safe, stop on repeated errors, stop on reconciliation failure.
- Required approvals before use: explicit user approval after paper observation, intent validation, simulation, kill-switch review, and API key safety review.

### RestrictedLiveAdapter

- Allowed inputs: none for the current project state.
- Allowed outputs: none for the current project state.
- Forbidden operations: all live exchange orders, live account reads, live balance reads, live position management, live cancellations, live retries, live reconciliation.
- Credential requirements: live keys are forbidden for now.
- Order placement capability: explicitly forbidden.
- Logging/audit requirements: not applicable until a separate future approval and design review exists.
- Failure handling: fail closed; any accidental live-adapter path must be treated as a safety issue.
- Required approvals before use: not approved; live adapter discussion requires a separate manual approval checkpoint after testnet lifecycle validation.

## Boundary Rules

- Current MVP may only use `PaperAdapter` behavior and reporting components.
- `OrderIntentWriter` may write non-executing intent files only after separate approval.
- `SimulatedDryRunAdapter` may simulate fills only from local data.
- `TestnetAdapter` is future-only and approval-gated.
- `RestrictedLiveAdapter` is future-only and explicitly forbidden for now.
- No private exchange call may be introduced without a separate approved task.
- Adapter mode must be explicit in every record and log.
- Adapter mode must never be inferred from the presence of credentials.
- Any unknown adapter mode must fail closed.
- Any adapter receiving `BLOCK`, `stale_data`, malformed state, or unresolved risk flags must refuse action.

## Audit Boundary

Every future adapter event must record:

- adapter name and mode,
- source signal/risk/response identifiers,
- source order intent identifier when applicable,
- timestamp,
- symbol and instrument,
- decision/action,
- safety gates evaluated,
- kill-switch state,
- result,
- redacted error if any.

Secrets must never be logged.

## Approval Gates

Moving from one adapter boundary to the next requires explicit approval:

1. Paper reports only.
2. Non-executing order intent writing.
3. Local simulated dry-run fills.
4. Testnet adapter skeleton.
5. Testnet lifecycle validation.
6. Separate live-adapter discussion.

The current task completes only design documentation. No adapter implementation is added.
