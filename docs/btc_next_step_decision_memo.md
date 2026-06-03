# BTC Next-Step Decision Memo

## Purpose

This memo reviews whether the next step after the completed 24h VM paper observation should be more paper observation, a non-executing `OrderIntentWriter` proposal, implementation of that writer, or any testnet/live path.

This memo is review/proposal only. It does not implement an `OrderIntentWriter`, write `runtime/order_intents/`, add adapters, call private APIs, use API keys, read account balances, place orders, add testnet/live trading, optimize thresholds, claim profitability, or claim execution readiness.

## Current Status

The BTC paper-mode MVP currently supports public BTCUSDT 4h data refresh, deterministic Long1-only signal checks, risk and response decisions, paper state/logs, monitoring/status/daily review reports, alert summaries, operator checklists, order-intent design docs, a non-executing order-intent schema, schema audit, writer design review, and a Google Cloud paper-observation guide.

One completed 24h VM observation is documented in [BTC Multi-Day Paper Observation Plan](btc_multi_day_paper_observation_plan.md#completed-vm-observation-example-2026-06-02-to-2026-06-03).

## Evidence From Completed 24h VM Observation

- Observation duration: `24.0018` hours.
- Cycles completed: `7`.
- Public data refresh: `7/7` success.
- `stale_data` count: `0`.
- Signal counts: `WAIT=7`, `LONG1=0`.
- Response counts: `WATCH=7`, `PAPER_LONG=0`, `BLOCK=0`.
- Risk levels: `HIGH=7`, `BLOCK=0`.
- Dominant risk flags: `extreme_distance_from_ema50=7`, `weekly_daily_regime_mismatch=7`.
- Alerts: `INFO=7`, `WARN=0`, `BLOCKED=0`.
- Operator checklist: `INFO=7`.
- Paper state stayed closed and internally consistent.
- No order intents, adapters, private APIs, API keys, account reads, order placement, testnet trading, or live trading were used.

## What The Observation Proves

- The paper workflow can run unattended on a VM for one full day.
- Public BTCUSDT 4h refresh worked repeatedly without API keys.
- The signal/risk/response/reporting sequence completed consistently.
- `stale_data` cleared after refresh and remained clear during this window.
- Paper state remained consistent while no entry signal occurred.
- Alert and checklist output stayed explainable.

This is operational stability evidence for one paper-only window.

## What The Observation Does Not Prove

- It does not prove profitability.
- It does not validate trade entry behavior because `PAPER_LONG=0`.
- It does not validate paper exit behavior.
- It does not prove that Long1 behaves well across regimes.
- It does not validate edge cases such as stale data returning, malformed logs, duplicate paper position, drawdown guard, or sudden signal/risk changes.
- It does not justify testnet readiness or live readiness.

`PAPER_LONG=0` matters because no intent-worthy entry scenario occurred. Without at least one explainable paper entry or a clearly defined no-entry intent scenario, a runtime writer would mostly produce `NONE` or `WATCH_ONLY` records and would not yet validate the more important transition behavior around entry, duplicate-position blocking, invalidation, or paper-state changes.

## Option A: Continue Paper Observation

Continue VM or local paper observation for 2-3 more days using the existing command index and observation plan.

Pros:

- Builds evidence across more completed 4h candles.
- Increases chance of seeing regime/risk changes.
- Tests repeated fresh-data cycles and daily review comparisons.
- Keeps implementation risk low.
- Preserves the current safety boundary.

Cons:

- Does not add new capability.
- May still produce no `PAPER_LONG` if Long1 conditions remain incomplete.

Assessment: recommended.

## Option B: Draft Non-Executing Writer Proposal Only

Draft an implementation proposal for a future non-executing `OrderIntentWriter`, without writing runtime intents or adding code.

Pros:

- Clarifies exact future implementation boundaries.
- Can define tests and fixture requirements before code exists.
- Keeps the writer blocked while evidence remains thin.

Cons:

- Does not collect more market-operation evidence.
- May be premature because no `PAPER_LONG` or intent-worthy scenario was observed.

Assessment: acceptable only as a proposal, not implementation.

## Option C: Implement OrderIntentWriter Now

Add a runtime writer that creates non-executing intent files.

Pros:

- Would test schema integration and append-only file behavior.

Cons:

- Premature because only one 24h window exists.
- No `PAPER_LONG` occurred.
- Entry and paper-state transition behavior remain untested by observation.
- Adds more runtime surface before the need is proven.

Assessment: no-go for now.

## Option D: Testnet Or Live Path

Move toward testnet or live trading.

Assessment: no-go.

Missing before testnet:

- Runtime writer implementation and tests.
- Simulated dry-run adapter design/testing.
- Reconciliation design.
- Failure-mode tests.
- Kill-switch verification.
- Explicit approval.

Live trading remains forbidden. There is no current basis for live execution discussion.

## Recommended Next Step

Continue paper observation for 2-3 more days before implementing an `OrderIntentWriter`.

Optionally, draft a non-executing writer proposal only, but keep implementation blocked. The safest combined path is:

1. Continue paper observation for 2-3 more days.
2. Keep schema audit and writer design review at `PASS`.
3. Record whether any `PAPER_LONG`, new risk state, stale-data recurrence, or paper-state transition occurs.
4. Draft a writer proposal only if observation reveals a clear operational need.
5. Do not implement writer, simulated adapter, testnet, or live trading yet.

## Go/No-Go Criteria

Go for a writer proposal only when:

- Multi-day paper observation remains stable.
- Public data refresh succeeds repeatedly.
- `stale_data` remains explainable and clears after refresh.
- Paper state remains consistent.
- Schema audit remains `PASS`.
- Writer design review remains `PASS`.
- At least one explainable `PAPER_LONG` occurs, or there is a clear intent-worthy scenario that justifies recording `NONE`/`WATCH_ONLY` intents.

No-go for writer implementation when:

- There is only one completed 24h paper window.
- `PAPER_LONG=0` and no intent-worthy scenario exists.
- Risk remains persistently `HIGH` without broader observation context.
- Paper state transitions have not been observed.
- Any unexplained `WARN`, `BLOCKED`, malformed log, or stale-data behavior appears.

No-go for testnet when:

- No writer implementation and writer tests exist.
- No simulated dry-run adapter design/testing exists.
- No reconciliation design exists.
- Failure modes and kill switches are unverified.
- Explicit approval has not been granted.

No-go for live:

- Live remains forbidden.

## Suggested Next Codex Prompt

```text
Continue BTC VM paper observation for 2-3 more days using the existing safe paper-only workflow, then summarize whether any PAPER_LONG, new risk state, stale-data recurrence, or paper-state transition occurred. Do not implement OrderIntentWriter, adapters, testnet, or live trading.
```

## Decision

Continue paper observation. A non-executing `OrderIntentWriter` proposal may be drafted in parallel only if it remains design-only. Do not implement the writer yet. Do not move to testnet or live trading.
