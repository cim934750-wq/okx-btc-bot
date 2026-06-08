# BTC OrderIntentWriter Decision Memo

## Purpose

This memo decides whether the BTC paper-mode MVP should continue observation, draft a design-only non-executing `OrderIntentWriter` proposal, or implement a runtime writer now.

This is docs/review only. It does not implement an `OrderIntentWriter`, create `runtime/order_intents/`, add exchange adapters, call private APIs, use API keys, read account balances, place orders, add testnet/live trading, change strategy parameters, optimize thresholds, claim profitability, or claim testnet/live readiness.

## Current Paper Evidence

The MVP has completed one documented 24-hour VM paper observation and one documented 72-hour VM paper observation.

### Completed 24h Observation

- Elapsed time: `24.0018` hours.
- Cycles completed: `7`.
- Public data refresh: `7/7` success.
- `stale_data_count`: `0`.
- Signal counts: `WAIT=7`, `LONG1=0`.
- Response counts: `WATCH=7`, `PAPER_LONG=0`, `BLOCK=0`.
- Risk levels: `HIGH=7`.
- Paper state: closed and internally consistent.
- Runtime order intents: absent.
- Private API, API keys, account reads, order placement, adapters, testnet, and live trading: absent.

### Completed 72h Observation

- Elapsed time: `72.0013` hours.
- Cycles completed: `19`.
- Signal counts: `WAIT=19`, `LONG1=0`.
- Response counts: `WATCH=19`, `PAPER_LONG=0`, `BLOCK=0`.
- Risk levels: `HIGH=19`.
- Dominant risk flags: `extreme_distance_from_ema50=19`, `weekly_daily_regime_mismatch=19`.
- `stale_data_count`: `0`.
- Alerts: `INFO=3`, `WARN=16`, `BLOCKED=0`.
- WARNs were stale-threshold proximity behavior, not actual `stale_data`.
- Paper state: closed and internally consistent.
- Runtime order intents: absent.
- Private API, API keys, account reads, order placement, adapters, testnet, and live trading: absent.

## What The Observations Prove

- The public-data refresh and paper workflow can run on a VM across documented 24h and 72h windows.
- The paper command chain can refresh data, run deterministic Long1 checks, assess risk, choose responses, log decisions, produce reviews, summarize alerts, and keep local paper state consistent.
- `stale_data` stayed clear during the documented windows.
- The system stayed conservative: all observed signal decisions were `WAIT`, all responses were `WATCH`, and all risk levels were `HIGH`.
- No code path created order intents, touched credentials, called private APIs, placed orders, or used testnet/live trading.

## What The Observations Do Not Prove

- They do not prove profitability.
- They do not validate Long1 entry behavior.
- They do not validate `PAPER_LONG` handling.
- They do not validate paper exit behavior.
- They do not validate duplicate-position blocking after a paper entry.
- They do not validate invalidation or drawdown transitions.
- They do not prove testnet readiness.
- They do not prove live readiness.

## Why PAPER_LONG=0 Matters

`PAPER_LONG=0` means no observed market state caused the current deterministic Long1 model and risk/response rules to create a paper entry.

That matters because a runtime `OrderIntentWriter` would mostly produce `NONE` or `WATCH_ONLY` records under the current evidence. It would not yet validate the more important writer behavior around an explainable entry, duplicate paper-position blocking, paper-state transition consistency, invalidation, or exit-warning paths.

Until at least one explainable `PAPER_LONG` or another clearly defined intent-worthy scenario appears, runtime writer implementation would add operational surface before the system has demonstrated the conditions that the writer is supposed to record.

## Should We Continue Paper Observation?

Yes.

Continue paper observation until the system sees more market contexts and, ideally, at least one explainable `PAPER_LONG` or other clear intent-worthy scenario. Observation should keep using the existing public-data, no-key, paper-only command workflow.

## Should We Draft A Design-Only Non-Executing Writer Proposal?

Yes, this is acceptable if it remains design-only.

A design-only proposal could safely cover:

- exact source inputs from decision logs, status snapshots, daily reviews, alert summaries, and paper state,
- append-only runtime path design,
- canonical JSON serialization and checksum rules,
- schema validation requirements,
- blocked-intent behavior for `stale_data`, response `BLOCK`, risk `BLOCK`, malformed state, and duplicate paper positions,
- fixture-only test plan for valid and invalid non-executing records,
- operator review and audit requirements,
- explicit non-goals for adapters, private APIs, testnet, and live trading.

## What A Design-Only Proposal Must Not Do

A proposal must not:

- create `runtime/order_intents/`,
- write actual runtime intent files,
- add `OrderIntentWriter` runtime code,
- add exchange adapters,
- add simulated, testnet, or live order execution,
- call private APIs,
- require or store API keys,
- read account balances,
- place, cancel, or reconcile orders,
- change strategy thresholds,
- promote `PAPER_LONG` to execution,
- claim execution readiness.

## Should We Implement OrderIntentWriter Now?

No.

Runtime implementation remains blocked because:

- `PAPER_LONG=0` across the documented 24h and 72h observations,
- no clearly intent-worthy entry scenario has been observed,
- paper entry, exit, duplicate-position, and invalidation transitions remain unvalidated,
- risk stayed `HIGH` across all observed checks,
- adding writer runtime behavior now would create more operational surface without evidence that it is needed.

## Evidence Required Before Runtime Implementation

Runtime writer implementation should be considered only when all of these are true:

- multi-day paper observation remains stable,
- repeated public data refreshes stay fresh or produce expected-WARN behavior only,
- paper state remains consistent,
- schema audit remains `PASS`,
- writer design review remains `PASS`,
- at least one explainable `PAPER_LONG` occurs, or a clearly defined intent-worthy no-entry event exists,
- `BLOCK` and `stale_data` behavior remain stronger than any intent path,
- explicit user approval is given for writer implementation.

## Evidence Required Before Testnet

Testnet remains blocked until at least these are proven:

- runtime writer is implemented, non-executing, and fully tested,
- intent files remain append-only and schema-valid,
- simulated dry-run adapter design and tests exist,
- no private API code is added without explicit approval,
- order lifecycle tests are designed for create, acknowledge, partial fill, full fill, cancel, reject, timeout, retry, and reconcile,
- kill switches and safety gates are reviewed,
- tiny-notional testnet scope is explicitly approved.

## Why Live Remains Forbidden

Live trading remains forbidden because the current system has not validated profitability, entry behavior, exits, reconciliation, kill switches under real execution conditions, account safety, or failure modes. No live adapter, private API access, account access, or order placement exists in the MVP.

## Go Criteria For Future Writer Implementation

Go only if all are true:

- multi-day paper observation remains stable,
- repeated data refreshes stay fresh or expected-WARN only,
- paper state remains consistent,
- schema audit remains `PASS`,
- writer design review remains `PASS`,
- at least one explainable `PAPER_LONG` or clearly defined intent-worthy event exists,
- `BLOCK` and `stale_data` behavior remain stronger than any intent path,
- explicit approval is given.

## No-Go Criteria

No-go if any are true:

- `PAPER_LONG=0` and no clear intent-worthy scenario exists,
- `stale_data` recurs unexpectedly,
- paper state becomes inconsistent,
- `WARN` or `BLOCK` becomes unexplained,
- any order-intent path could bypass review,
- any code path touches private APIs, credentials, account data, adapters, testnet, or live trading.

## Recommended Next Step

Continue paper observation as the primary next step.

In parallel, drafting a design-only non-executing `OrderIntentWriter` proposal is acceptable if it is explicitly limited to review, fixtures, schema validation expectations, append-only constraints, and safety gates. Runtime implementation should remain blocked. Testnet and live trading should remain blocked.

## Decision

- Continue paper observation: yes.
- Draft a design-only non-executing writer proposal: acceptable.
- Implement `OrderIntentWriter` now: no.
- Move toward testnet/live: no.
