# BTC Intent-Worthy Scenario Checklist

## Purpose

This read-only checklist defines the evidence that would make a future BTC
Long1 or `PAPER_LONG` scenario worth reviewing. It exists to decide whether a
new bounded observation window or later design-only fixture review would add
useful evidence.

This checklist is not a trading signal, an order-intent record, an approval to
implement `OrderIntentWriter`, or an approval to use testnet or live trading.
It does not change strategy thresholds, Long1 conditions, risk rules, response
rules, paper-state behavior, or safety gates.

Current context:

- The paper observation workflow is operationally stable.
- Completed 24h and 72h observations produced only `WAIT` and `WATCH`.
- `LONG1=0` and `PAPER_LONG=0` across the documented runs.
- Observation is paused and the VM is stopped.
- No runtime writer, adapter, private API, or execution path exists.
- `runtime/order_intents/` remains absent.

Related documents:

- [BTC Research Pause And Decision Checkpoint](btc_research_pause_decision_checkpoint.md)
- [BTC Multi-Day Paper Observation Plan](btc_multi_day_paper_observation_plan.md)
- [BTC Signal Response MVP](btc_signal_response_mvp.md)
- [BTC OrderIntentWriter Decision Memo](btc_order_intent_writer_decision_memo.md)
- [BTC OrderIntentWriter Design Proposal](btc_order_intent_writer_design_proposal.md)
- [BTC Paper-Mode Command Index](btc_paper_mode_command_index.md)

## Checklist Use

Apply this checklist only to existing paper outputs or to a separately approved
future paper observation. Do not restart a VM merely to complete the checklist.

For each item, record one of:

- `PASS`: required evidence is present and internally consistent.
- `EXPECTED_WARN`: a documented, non-blocking warning is present.
- `FAIL`: evidence is missing, malformed, stale, contradictory, or blocked.
- `NOT_APPLICABLE`: the item does not apply to the scenario category.

Any unknown safety result is `FAIL`. A scenario cannot be classified as
intent-worthy when a required freshness, provenance, paper-state, or blocking
condition fails.

## Required Data Freshness Conditions

A scenario cannot be intent-worthy unless all required freshness checks pass:

- [ ] The latest candle is complete and fresh under the existing stale-data
  rule.
- [ ] `stale_data_count=0` for the relevant observation scope.
- [ ] No active `stale_data` risk flag exists.
- [ ] The most recent refresh attempt succeeded.
- [ ] The latest candle timestamp is recorded in UTC.
- [ ] The latest candle age is recorded.
- [ ] The refresh timestamp and refresh result are recorded.
- [ ] The data source path is recorded.
- [ ] No malformed signal, status, review, alert, checklist, or paper-state
  output exists.
- [ ] No refresh gap or duplicate warning makes the latest decision
  uninterpretable.

If stale data, an incomplete candle, a failed refresh, or malformed output is
present, classify the scenario as Category D and produce `NO_ACTION` or
`PAUSE_AND_REVIEW`.

## Required Signal Conditions

These conditions describe review evidence. They do not add thresholds or alter
the current Long1 rules.

- [ ] `long1_active`, signal decision, confidence, passed conditions, and
  missing conditions are recorded from existing outputs.
- [ ] The signal source path, run timestamp, and candle timestamp are recorded.
- [ ] The signal decision is explainable from the existing documented Long1
  conditions.
- [ ] Confidence is a recognized value and is not missing or malformed.
- [ ] The decision uses a completed, fresh candle.
- [ ] The decision was not caused by stale, incomplete, synthetic, or inferred
  data.
- [ ] If `Long1` is active, all passed conditions and any remaining discrepancy
  are captured.
- [ ] If the case is a near miss, the exact existing missing conditions are
  captured without inventing a new threshold or reinterpretation.

A review-worthy signal condition is one of:

- An observed existing-output `Long1` activation.
- An observed `PAPER_LONG` response.
- A near-Long1 case where the current outputs explicitly show which existing
  conditions passed and which remained missing.

`WAIT` alone is not intent-worthy unless it belongs to a documented blocked,
stale, or paper-state rejection case that provides new safety evidence.

## Required Risk Conditions

A scenario is stronger when risk is `LOW` or `MEDIUM`. Risk does not authorize
an intent; it only affects review quality.

- [ ] Risk level and all risk flags are recorded.
- [ ] No risk level `BLOCK` exists.
- [ ] No unexplained risk flag exists.
- [ ] `HIGH` risk is absent, or its reason is explicit and transient.
- [ ] `weekly_daily_regime_mismatch` is absent, or its effect on the response is
  explicitly documented.
- [ ] `extreme_distance_from_ema50` is absent, or its transient occurrence and
  resolution are documented.
- [ ] Sudden volatility, invalid ATR, drawdown, cooldown, and duplicate-position
  flags are recorded when present.
- [ ] The risk output refers to the same run and candle as the signal output.

Risk interpretation rules:

- `LOW` or `MEDIUM` with no blocking flags supports deeper review.
- `HIGH` can support a Category C safety review, but it cannot support a
  writer-implementation decision.
- Risk `BLOCK` always overrides the signal and response path.
- An unexplained flag requires `PAUSE_AND_REVIEW`.

## Required Response Conditions

An intent-worthy review requires one of these existing response outcomes:

- `PAPER_LONG`; or
- a response close to `PAPER_LONG` under the existing documented decision
  rules, with all remaining blockers named by current outputs; or
- `WATCH` where the reason preventing `PAPER_LONG` is explicit and provides
  useful evidence about signal, risk, or paper-state gating.

Required checks:

- [ ] Response action and response reason are recorded.
- [ ] Response source/run/candle identity matches the signal and risk outputs.
- [ ] `PAPER_LONG`, when present, is explainable from existing signal and risk
  rules.
- [ ] `WATCH`, when reviewed as a near miss, names the exact current blockers.
- [ ] Response `BLOCK` forces no intent path and no action.
- [ ] Active `stale_data` forces no intent path and no action.
- [ ] No response is manually promoted from `WAIT` or `WATCH`.

## Paper-State Conditions

The paper-state snapshot must be present and internally consistent.

- [ ] `open_position` is recorded.
- [ ] Position side, entry timestamp, and entry price agree with
  `open_position`.
- [ ] Paper equity and max drawdown are valid numbers.
- [ ] The paper-state source path is recorded.
- [ ] The paper state agrees with recent decision logs.
- [ ] Duplicate open-position risk is explicitly checked.
- [ ] Any prior signal time or state transition is explainable.

A scenario is invalid when:

- Paper state is missing or malformed.
- `open_position=false` conflicts with populated side or entry fields.
- `open_position=true` lacks coherent side or entry fields.
- Equity or drawdown fields are malformed.
- A duplicate position is possible but the duplicate gate is unclear.
- Decision logs and paper state disagree.

Invalid paper state is Category E and permits only `PAUSE_AND_REVIEW` or
`NO_ACTION`.

## Alert And Checklist Conditions

- [ ] Alert severity is recorded.
- [ ] Operator checklist severity is recorded.
- [ ] `INFO` or an expected, documented `WARN` is preferred.
- [ ] Every `WARN` reason is captured and explainable.
- [ ] Approaching-stale warnings are distinguished from actual `stale_data`.
- [ ] No `BLOCKED` alert exists for Category A or B.
- [ ] No unexplained warning exists.
- [ ] Recommended human action remains paper-only and non-executing.

An expected warning can support review. An unexplained warning requires
`PAUSE_AND_REVIEW`. `BLOCKED` always prevents an intent path.

## Intent-Worthy Categories

### Category A: Observed PAPER_LONG Event

Required evidence:

- Existing output reports `PAPER_LONG`.
- Signal, risk, response, and paper-state artifacts refer to the same run and
  completed candle.
- Data freshness checks pass.
- Risk is not `BLOCK`.
- Paper state transition is explicit and internally consistent.
- Alert/checklist output explains the event.
- No duplicate-position conflict exists.

Allowed decisions:

- `PAUSE_AND_REVIEW`
- `DESIGN_ONLY_FIXTURE_CANDIDATE`
- `WRITER_PROPOSAL_REVIEW_CANDIDATE`

Forbidden:

- Implementing a writer.
- Creating runtime order intents.
- Starting testnet/live.
- Placing an order.
- Claiming the event is profitable.

### Category B: Near-Miss Long1 Review Case

Required evidence:

- Existing outputs show a near-Long1 state through passed and missing
  conditions.
- The missing conditions and response reason are explicit.
- Data is fresh and outputs are consistent.
- Risk is `LOW`, `MEDIUM`, or explainably transient `HIGH`.
- Paper state remains coherent.

Allowed decisions:

- `CONTINUE_OBSERVATION` for a named, bounded evidence target.
- `PAUSE_AND_REVIEW`
- `DESIGN_ONLY_FIXTURE_CANDIDATE`
- `NO_ACTION`

Forbidden:

- Reclassifying the case as `PAPER_LONG`.
- Changing thresholds to force a signal.
- Writer implementation or execution work.

### Category C: Blocked-By-Risk Case

Required evidence:

- Signal evidence is otherwise reviewable.
- Risk level/flags and blocked reason are explicit.
- Response gating is traceable to the documented risk rules.
- No manual override occurred.

Allowed decisions:

- `PAUSE_AND_REVIEW`
- `DESIGN_ONLY_FIXTURE_CANDIDATE`
- `NO_ACTION`

Forbidden:

- Any intent path.
- Whitelisting or suppressing the flag.
- Threshold changes, writer implementation, testnet, or live trading.

### Category D: Stale-Data Rejection Case

Required evidence:

- Stale status, candle timestamp/age, refresh result, and blocked response are
  captured.
- The stale-data rule demonstrably dominates any signal.
- Any recovery refresh is documented separately.

Allowed decisions:

- `PAUSE_AND_REVIEW`
- `DESIGN_ONLY_FIXTURE_CANDIDATE`
- `NO_ACTION`

Forbidden:

- Any intent path.
- Forward-filling or inferring data.
- Overriding stale status.
- Treating a recovered later cycle as proof that the stale cycle was valid.

### Category E: Paper-State Rejection Case

Required evidence:

- The inconsistency or duplicate-position concern is identified.
- Signal/risk/response artifacts and the conflicting paper-state snapshot are
  preserved.
- The system fails closed.

Allowed decisions:

- `PAUSE_AND_REVIEW`
- `DESIGN_ONLY_FIXTURE_CANDIDATE`
- `NO_ACTION`

Forbidden:

- Editing paper state to manufacture consistency.
- Any intent path.
- Writer, adapter, testnet, or live implementation.

## Required Evidence Packet

Any future scenario review must capture:

- [ ] Observation/run ID.
- [ ] Cycle ID.
- [ ] Review timestamp in UTC.
- [ ] Latest completed candle timestamp in UTC.
- [ ] Latest candle age.
- [ ] Data path and row count.
- [ ] Refresh summary and refresh exit status.
- [ ] Signal JSON or exact source output.
- [ ] Risk JSON or exact source output.
- [ ] Response JSON or exact source output.
- [ ] Paper-state snapshot.
- [ ] Monitoring summary.
- [ ] Daily review snapshot.
- [ ] Alert summary and severity.
- [ ] Operator checklist and severity.
- [ ] Stale status and stale-data count.
- [ ] Relevant decision log lines.
- [ ] Relevant stderr and command exit files.
- [ ] Passed and missing Long1 conditions.
- [ ] Active risk flags and warnings.
- [ ] Confirmation that `runtime/order_intents/` is absent.
- [ ] Confirmation that no private API, credentials, account reads, adapter,
  order placement, testnet, or live path was used.

The evidence packet should reference existing files. This checklist does not
authorize copying runtime artifacts into Git.

## Allowed Decision Outcomes

The checklist may produce only:

- `CONTINUE_OBSERVATION`: collect a bounded, predeclared window for a named
  evidence target.
- `PAUSE_AND_REVIEW`: stop collection and inspect inconsistent, blocked, or
  unusually important evidence.
- `DESIGN_ONLY_FIXTURE_CANDIDATE`: use the documented scenario as the basis for
  a future non-executing fixture design task.
- `WRITER_PROPOSAL_REVIEW_CANDIDATE`: revisit the existing writer proposal at
  the documentation/review level only.
- `NO_ACTION`: retain the evidence without further work.

The checklist must never produce:

- `IMPLEMENT_WRITER`
- `START_TESTNET`
- `START_LIVE`
- `PLACE_ORDER`

No checklist outcome is implementation approval.

## Go / No-Go Criteria

### GO For Renewed Observation

Renewed observation can be proposed only when:

- A plausible regime or completed-candle window is identified in advance.
- The expected evidence target is named, such as a near-Long1 transition,
  risk-flag resolution, or stale-data rejection/recovery case.
- Recent risk is preferably `LOW` or `MEDIUM`, with no unresolved `BLOCK`.
- VM duration, cost, cycle interval, and stop plan are defined.
- The VM remains stopped until explicit approval to start it.
- No thresholds or safety gates are changed.

### GO For Design-Only Fixture Planning

Fixture planning can be proposed only when:

- It is based on an observed or precisely defined scenario category.
- No runtime writer is created.
- No `runtime/order_intents/` path or file is created.
- No fixture code or tests are added without explicit approval.
- Schema and safety gates remain unchanged.
- The fixture remains non-executing and paper-only.

### NO-GO For Writer Implementation

Writer implementation remains blocked when:

- `PAPER_LONG=0`.
- No intent-worthy scenario packet exists.
- Paper-state transition behavior is unvalidated.
- Duplicate-position blocking is unvalidated.
- Exit and invalidation behavior is unvalidated.
- Stale-data and `BLOCK` dominance have not been demonstrated through approved
  scenario evidence or fixtures.
- Explicit implementation approval is absent.

### NO-GO For Testnet Or Live

Testnet and live trading are always blocked at this stage.

No checklist result can authorize adapters, credentials, account reads, order
placement, testnet, or live trading.

## Safety Boundary

The following constraints remain unchanged:

- No writer implementation.
- No `runtime/order_intents/` directory or files.
- No exchange adapter.
- No simulated adapter.
- No private API.
- No API keys or credentials.
- No account, balance, position, fill, or private order reads.
- No order placement, cancellation, amendment, or reconciliation.
- No testnet.
- No live trading.
- No strategy threshold changes.
- No parameter optimization or threshold sweeps.
- No VM restart from this checklist.
- No manual override of stale data, `WARN`, `BLOCK`, or risk flags.
- No profitability claims.
- No implementation, testnet, or live-readiness claims.

## Suggested Next Safe Prompt

> Use the BTC intent-worthy scenario checklist to evaluate whether another VM
> paper observation window is justified. Do not start the VM unless the
> checklist identifies a specific evidence target.
