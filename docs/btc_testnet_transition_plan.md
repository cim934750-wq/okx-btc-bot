# BTC Testnet Transition Plan

## Purpose

This document defines a future staged path from paper observation toward possible testnet validation. It is design-only. It does not implement testnet trading, private API access, live trading, or exchange order placement.

## Current State

The MVP is paper/dry-run only. It can refresh public BTCUSDT 4h data, evaluate Long1-only signals, run risk checks, write paper state/logs, produce monitoring/status/daily review reports, summarize alerts, and print operator checklists.

No API keys are required. No private API calls or exchange orders exist.

## Future Staged Path

1. Continue paper observation.
2. Add order intent writer only.
3. Add intent validation tests.
4. Add simulated dry-run adapter.
5. Add testnet adapter skeleton only after explicit approval.
6. Validate testnet order lifecycle.
7. Run testnet only with tiny notional.
8. Produce testnet audit report.
9. Require manual approval before any live adapter discussion.

## Stage Details

### 1. Continue Paper Observation

- Refresh public BTC data manually or on an approved local schedule.
- Run one signal check after completed 4h candles.
- Review status dashboard, monitoring report, daily review, alert summary, and operator checklist.
- Keep runtime logs and paper state under local runtime paths.
- Do not trade.

### 2. Add Order Intent Writer Only

- Write append-only non-executing order intent records.
- Require `execution_allowed=false`.
- Require source decision logs and snapshots.
- Require blocked reasons for unsafe states.
- Do not call private APIs.
- Do not place orders.

### 3. Add Intent Validation Tests

- Validate required fields.
- Validate canonical hashing/checksum behavior.
- Validate `execution_allowed=false` for the current version.
- Validate stale data, `BLOCK`, malformed state, duplicate position, and unresolved risk flags block execution.
- Validate no credential fields are allowed.

### 4. Add Simulated Dry-Run Adapter

- Simulate fills only from local OHLCV data.
- Reference order intents and candle timestamps.
- Simulate create, acknowledge, partial fill, full fill, cancel, reject, timeout, retry, and reconcile states locally.
- Produce local audit reports.
- Do not call private APIs.

### 5. Add Testnet Adapter Skeleton After Approval

- Add only after explicit user approval.
- Use testnet credentials from environment variables only.
- Keep testnet and live credentials separate.
- Include no live endpoint path.
- Include kill-switch and safety-gate checks before any private call.

### 6. Validate Testnet Order Lifecycle

The testnet lifecycle must cover:

- create,
- acknowledge,
- partial fill,
- full fill,
- cancel,
- reject,
- timeout,
- retry,
- reconcile.

Each lifecycle event must be logged with secret redaction and source intent linkage.

### 7. Run Testnet Only With Tiny Notional

- Use a tiny explicit notional cap.
- Require operator approval for the cap.
- Stop on any unexpected state, stale data, repeated error, reconciliation mismatch, or kill-switch trigger.

### 8. Produce Testnet Audit Report

The report must include:

- source intents,
- safety gates evaluated,
- kill-switch states,
- testnet order lifecycle events,
- reconciliation results,
- failures and retries,
- notional caps,
- unresolved risks,
- manual operator approval records.

### 9. Require Manual Approval Before Live Discussion

Live trading remains forbidden in this task. A future live adapter discussion requires a separate manual approval checkpoint after testnet lifecycle validation.

## Must Be Proven Before Testnet

- Multi-day paper observation logs exist.
- Data refresh is stable.
- No unexplained `BLOCK` or `WARN` states remain.
- Paper entries/exits behave as expected.
- Order intent schema is stable.
- Operator checklist is stable.
- Kill switch design has been reviewed.
- API key safety checklist has been reviewed.
- Runtime logs do not contain secrets.
- Secret scanning has been run before adding private API code.

## Must Be Proven Before Live

- Live remains forbidden in this task.
- Testnet lifecycle passes.
- Reconciliation passes.
- Kill switches are verified.
- Failure modes are tested.
- Max notional cap is enforced.
- Manual approval checkpoint is passed.
- No unresolved strategy validation issues remain.
- Profitability is still not assumed.

## Stop Conditions

Stop the transition process when:

- stale data persists after refresh,
- daily review remains `BLOCKED`,
- risk level remains `BLOCK`,
- paper state is inconsistent,
- intent validation fails,
- simulated fills diverge from expected local data behavior,
- testnet lifecycle cannot reconcile,
- API-key safety review fails,
- operator approval is missing.

## Non-Goals

- No testnet implementation in this task.
- No live implementation in this task.
- No private API keys.
- No account data.
- No exchange orders.
- No production deployment.
- No profitability claims.
