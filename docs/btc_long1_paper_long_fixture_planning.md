# BTC Long1 And PAPER_LONG Fixture Planning

## Purpose

This memo defines how future BTC Long1 and `PAPER_LONG` review cases could be
represented as non-executing, test-only fixtures after separate explicit
approval.

This is a design-only planning artifact. It does not create fixture files,
tests, runtime files, an `OrderIntentWriter`, or order-intent records. It does
not start the VM, restart observation, change strategy thresholds, or authorize
testnet or live trading.

Current evidence remains:

- The completed 24h observation produced `WAIT=7`, `WATCH=7`, and
  `PAPER_LONG=0`.
- The prior 72h observation produced `WAIT=19`, `WATCH=19`, and
  `PAPER_LONG=0`.
- The latest 72h observation produced `WAIT=18`, `WATCH=18`, and
  `PAPER_LONG=0`.
- Paper state remained closed and consistent.
- `runtime/order_intents/` remains absent.
- The VM observation is paused and the VM must remain stopped.

Related documents:

- [BTC Intent-Worthy Scenario Checklist](btc_intent_worthy_scenario_checklist.md)
- [BTC Next Observation Justification Review](btc_next_observation_justification_review.md)
- [BTC Research Pause And Decision Checkpoint](btc_research_pause_decision_checkpoint.md)
- [BTC OrderIntentWriter Design Proposal](btc_order_intent_writer_design_proposal.md)
- [BTC OrderIntentWriter Decision Memo](btc_order_intent_writer_decision_memo.md)
- [BTC Order Intent Design](btc_order_intent_design.md)

## Why Fixtures Are Useful

Real observation has not produced `PAPER_LONG`. More arbitrary VM uptime is not
currently justified, and thresholds must not be changed to manufacture an
event.

Planning fixtures now can:

- Define the evidence packet expected from a future observed Long1,
  `PAPER_LONG`, near-miss, or fail-closed case.
- Make future schema and safety review deterministic.
- Separate market evidence from deliberately synthetic safety cases.
- Expose missing provenance before any fixture implementation is approved.
- Prepare review logic without creating an intent writer or execution path.

Fixture planning does not prove that a market event occurred, that a strategy
is profitable, or that any runtime component is ready.

## Fixture Categories

The following categories are planning labels only. No corresponding files are
created by this memo.

### Expected State And Decision Matrix

| Fixture category | Intended purpose | Required source artifacts | Expected signal state | Expected risk state | Expected response action | Expected paper state | Expected alert/checklist severity | Allowed decision outcome | Forbidden outcomes | Required safety assertions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `OBSERVED_PAPER_LONG` | Preserve a naturally observed `PAPER_LONG` event for review of cross-artifact consistency. | Full observation packet, schema validation result, logs, and explicit no-intent/no-private-path confirmations. | `LONG1`, `long1_active=true`, with passed and missing conditions matching the existing strategy output. | `LOW` or `MEDIUM`; never `BLOCK`; all flags explained. | `PAPER_LONG`. | Coherent pre-event closed state and, if produced by the paper engine, coherent post-event paper transition. | `INFO` or explained `WARN`; never unexplained `BLOCKED`. | `PAUSE_AND_REVIEW`, `DESIGN_ONLY_FIXTURE_CANDIDATE`, or `WRITER_PROPOSAL_REVIEW_CANDIDATE`. | `IMPLEMENT_WRITER`, `START_TESTNET`, `START_LIVE`, `PLACE_ORDER`, profitability claims. | Fresh completed candle; same run/candle identity; `execution_allowed=false`; operator review; no private or execution path. |
| `NEAR_MISS_LONG1` | Preserve an explicit near-Long1 case without reclassifying it as a signal. | Full observation packet with passed and missing conditions and response reason. | Normally `WAIT` with `long1_active=false`; exact existing missing conditions recorded. | `LOW`, `MEDIUM`, or explained transient `HIGH`; not `BLOCK`. | `WATCH` or `WAIT`. | Closed and internally consistent. | `INFO` or explained `WARN`. | `NO_ACTION`, `CONTINUE_OBSERVATION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | Manual promotion to `LONG1` or `PAPER_LONG`, threshold changes, writer implementation. | No inferred conditions; no threshold reinterpretation; fresh data; deterministic source references. |
| `BLOCKED_BY_RISK` | Verify that an otherwise reviewable signal cannot bypass a blocking risk result. | Full observation packet plus the exact blocking flag and risk explanation. | `LONG1` or a reviewable near miss may be present. | `BLOCK`, or another risk state with an explicit current rule requiring rejection. | `BLOCK`. | Closed or unchanged; no new paper position. | `BLOCKED` or explained `WARN` consistent with the risk output. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | Any intent path, risk override, flag suppression, writer implementation, order placement. | `BLOCK` overrides all intent paths; intended action remains `NONE`; no state mutation. |
| `STALE_DATA_REJECTION` | Verify fail-closed behavior when source data is stale. | Signal/risk/response artifacts, candle metadata, refresh summary, stale status, and logs proving the stale condition. | `NO_SIGNAL`, `WAIT`, or otherwise rejected; never treated as actionable. | Contains `stale_data`; risk may be `BLOCK`. | `BLOCK` or another existing no-action response required by the stale-data rule. | Closed or unchanged. | `BLOCKED` or explained `WARN`. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | `PAPER_LONG`, any intent action, forward-filling evidence, threshold changes. | `stale_data` forces no intent; incomplete/future candles are excluded; no forward-fill. |
| `PAPER_STATE_REJECTION` | Verify rejection of missing, malformed, contradictory, or untraceable paper state. | Full observation packet plus malformed or inconsistent paper-state evidence and validation errors. | Any signal state is non-authoritative after the state failure. | `BLOCK` or explicit paper-state rejection flag if produced by existing logic. | `BLOCK` or no action. | Missing, malformed, or inconsistent by design; never silently repaired. | `BLOCKED` or explained `WARN`. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | State repair by inference, `PAPER_LONG`, writer implementation, order placement. | Inconsistent state rejects; source failure is explicit; no position transition is synthesized. |
| `DUPLICATE_POSITION_REJECTION` | Verify that an existing open paper position prevents a second long path. | Full observation packet plus coherent open-position snapshot and duplicate-position gate evidence. | `LONG1` may be active or a repeated long request may be represented. | Explicit duplicate-position risk or `BLOCK`. | `BLOCK` or no action under the existing duplicate-position rule. | Already open and coherent; remains unchanged. | `BLOCKED` or explained `WARN`. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | A second long, averaging down, duplicate intent, state mutation, order placement. | Duplicate position risk rejects; one-position invariant holds; no second intent path. |
| `WATCH_ONLY_MEDIUM_RISK` | Preserve the common stable observation state for regression comparison. | Full observation packet and alert/checklist summary. | Usually `WAIT`; exact passed and missing conditions retained. | `MEDIUM`, with every flag documented. | `WATCH`. | Closed and consistent. | `INFO` or explained `WARN`. | `NO_ACTION`, `CONTINUE_OBSERVATION`, or `PAUSE_AND_REVIEW`. | Promotion to `PAPER_LONG`, writer implementation, threshold changes. | Watch remains non-executing; no state transition; same run/candle provenance. |
| `WATCH_ONLY_HIGH_RISK` | Preserve a high-risk watch state and verify that high risk is not treated as readiness. | Full observation packet and complete risk-flag evidence. | Usually `WAIT`; any near-miss details remain descriptive only. | `HIGH`, with reasons explicit and no hidden override. | `WATCH` or `BLOCK` according to existing output. | Closed and consistent. | Explained `WARN` or `BLOCKED`. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | `PAPER_LONG`, writer implementation, risk suppression, readiness claims. | High risk cannot authorize intent; all flags are preserved; no manual promotion. |
| `MALFORMED_INPUT_REJECTION` | Verify rejection when required JSON, types, timestamps, or cross-artifact identity are malformed. | The malformed input, parse/validation result, related logs/stderr, and source identity when available. | `UNKNOWN` or not trusted. | `UNKNOWN` or `BLOCK`. | `BLOCK` or no action. | Not trusted; must remain unchanged. | `BLOCKED`. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | Defaulting malformed input into a valid signal, writer output, order placement. | Parsing fails closed; no guessed values; schema validation required; no state mutation. |
| `CREDENTIAL_FIELD_REJECTION` | Verify that credential-like fields are rejected by the closed schema boundary. | Negative schema candidate, schema validation result, and credential-field rejection evidence; no real secret values. | Not applicable to market evidence. | Not applicable; schema rejection occurs before intent review. | No response or intent is produced from the invalid candidate. | Unchanged. | `BLOCKED` or validation failure. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | Storing credentials, accepting unknown fields, writer output, private API access. | Use obvious fake placeholders only; `additionalProperties=false`; credential fields rejected; no secrets. |
| `TESTNET_LIVE_MODE_REJECTION` | Verify that `testnet` and `live` modes are rejected by the current schema. | Negative schema candidate, schema validation result, and allowed-mode evidence. | Not applicable to market evidence. | Not applicable; schema rejection occurs before intent review. | No response or intent is produced from the invalid candidate. | Unchanged. | `BLOCKED` or validation failure. | `NO_ACTION`, `PAUSE_AND_REVIEW`, or `DESIGN_ONLY_FIXTURE_CANDIDATE`. | Enabling testnet/live, writer implementation, adapter creation, order placement. | Current modes remain limited to `paper`, `order_intent_only`, and `simulated_dry_run`; execution stays forbidden. |

## Required Source Artifacts

A future observed or approved synthetic fixture should be assembled from an
immutable review packet. The packet should include:

- Signal decision JSON.
- Risk assessment JSON.
- Response action JSON.
- Paper-state snapshot.
- Latest completed candle metadata.
- Refresh summary.
- Stale status and stale-data count.
- Alert summary and operator checklist summary.
- Run and cycle metadata.
- Relevant logs and stderr.
- Order-intent schema validation result when the fixture exercises schema
  behavior.
- Confirmation that `runtime/order_intents/` does not exist.
- Confirmation that no private API, credential, account-read, adapter, order,
  testnet, or live path was used.

Every artifact should record or be associated with:

- Source path.
- UTC capture timestamp.
- Run identifier.
- Cycle identifier.
- Completed candle timestamp.
- Content hash when practical.
- Observed or synthetic classification.

Artifacts referring to different runs or candles must not be merged into one
fixture.

## Synthetic Fixture Constraints

Synthetic fixtures may be considered only after explicit approval. They must:

- Be clearly and repeatedly marked `synthetic`.
- Never be presented as observed market evidence.
- Never be used for profitability, expectancy, or performance claims.
- Preserve existing strategy parameters and thresholds.
- Represent only documented schema, safety, and review behavior.
- Avoid private exchange data and real credentials.
- Avoid creating `runtime/order_intents/`.
- Avoid invoking or bypassing an `OrderIntentWriter`.
- Avoid adapters, account reads, order placement, testnet, and live trading.
- Pass the same schema audit and writer design-review gates applicable to the
  planned behavior.
- Use deterministic, non-executing checksum behavior when a fixture includes a
  `checksum_or_hash` field.
- Keep any future fixture path under a test-only location approved in a
  separate task, never under runtime output.

A synthetic `OBSERVED_PAPER_LONG` fixture is a contradiction and must not use
that category. A synthetic equivalent must be labeled as a separately approved
simulation case and cannot satisfy the requirement for observed
`PAPER_LONG` evidence.

## Expected Future Decisions

Fixture review may produce only these decisions:

- `NO_ACTION`
- `CONTINUE_OBSERVATION`
- `PAUSE_AND_REVIEW`
- `DESIGN_ONLY_FIXTURE_CANDIDATE`
- `WRITER_PROPOSAL_REVIEW_CANDIDATE`

Fixture review must not produce:

- `IMPLEMENT_WRITER`
- `START_TESTNET`
- `START_LIVE`
- `PLACE_ORDER`

`WRITER_PROPOSAL_REVIEW_CANDIDATE` means only that the existing design-only
proposal may be reviewed against stronger evidence. It is not writer
implementation approval.

## Safety Assertions Checklist

Every future fixture must make the following assertions testable:

- [ ] `execution_allowed=false`.
- [ ] `operator_review_required=true`.
- [ ] No API keys, secrets, passphrases, tokens, or credential-like fields.
- [ ] No account, balance, position, fill, or private order reads.
- [ ] No exchange or simulated execution adapter.
- [ ] No private endpoints.
- [ ] No order placement, cancellation, amendment, or reconciliation.
- [ ] No testnet or live mode.
- [ ] `BLOCK` response overrides every intent path.
- [ ] `BLOCK` risk level overrides every intent path.
- [ ] `stale_data` forces intended action `NONE`.
- [ ] Missing or inconsistent paper state rejects the candidate.
- [ ] Duplicate open-position risk rejects a second long candidate.
- [ ] Schema validation is required where an order-intent-shaped object is
  represented.
- [ ] Unknown fields are rejected.
- [ ] Source paths and run/candle identities are internally consistent.
- [ ] Any checksum is deterministic over canonical, non-secret fields.
- [ ] No runtime file is created as part of fixture review.

An unknown assertion result is a failed assertion.

## Relationship To The OrderIntentWriter Proposal

Future fixtures could support review of the design-only
`OrderIntentWriter` proposal by providing stable examples for:

- Valid non-executing watch and block records.
- `PAPER_LONG` review shape after a real event is observed.
- `BLOCK` and `stale_data` fail-closed behavior.
- Malformed paper-state and duplicate-position rejection.
- Credential-field and live/testnet-mode rejection.
- Append-only and deterministic checksum expectations.

This memo does not approve writer implementation. The current absence of an
observed `PAPER_LONG`, combined with `runtime/order_intents/` remaining absent,
keeps runtime writer work blocked.

Any future implementation discussion requires:

- Explicit user approval.
- Observed or explicitly approved synthetic fixture evidence.
- A documented fixture purpose.
- Passing schema and writer-design safety review.
- A separate implementation decision.

Fixture implementation approval, if later granted, would still not approve a
runtime writer, adapter, testnet, live trading, or order placement.

## Go/No-Go Criteria

### GO For Future Fixture Implementation

Future test-only fixture implementation may be considered only when all of the
following are true:

- Explicit approval is given for named fixture files.
- Each fixture purpose and observed/synthetic status is documented.
- Required source artifacts are available or an approved synthetic case is
  fully specified.
- No runtime files are created.
- No writer runtime is added.
- Existing schema constraints remain intact.
- Safety assertions are deterministic and testable.
- Fixture paths and staging scope are explicitly limited to test-only
  artifacts.

GO means permission to consider test-only fixtures. It does not mean
permission to implement a writer.

### NO-GO

Fixture implementation remains blocked if any of these conditions apply:

- A fixture could be mistaken for a live signal or observed event.
- A fixture requires private API access, credentials, or exchange account
  state.
- A fixture requires strategy threshold or parameter changes.
- A fixture implies profitability, trading readiness, or implementation
  readiness.
- A fixture creates or writes under `runtime/order_intents/`.
- A fixture bypasses operator review, schema validation, or writer-review
  gates.
- A fixture permits execution, adapter use, testnet, live trading, or order
  placement.
- Source artifacts from different runs or candles are combined.
- A synthetic case is used as proof that `PAPER_LONG` occurred.

## Recommended Next Step

- Keep the VM observation paused.
- Keep the VM stopped.
- Do not implement fixtures yet.
- Wait for either a naturally observed intent-worthy case or explicit approval
  to add named test-only fixtures.
- Keep `OrderIntentWriter`, adapters, testnet, live trading, and order
  placement blocked.

## Suggested Next Codex Prompt

> Review whether any test-only fixture files should be added for schema/safety
> validation, but do not add them without explicit approval.

## Current Decision

Decision: `PAUSE_AND_REVIEW`.

Implementation readiness: none. This memo is design-only and does not make the
system writer-ready, testnet-ready, or live-ready.
