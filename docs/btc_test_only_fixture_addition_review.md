# BTC Test-Only Fixture Addition Review

## Current Decision Question

Should the project add test-only fixture files now?

Decision: **No. Do not add fixture files yet.**

Test-only fixtures could later validate stable schema and safety behavior,
including rejection of unsafe fields and modes, fail-closed handling, and
cross-artifact review expectations. They would not validate market behavior,
Long1 edge, profitability, entry or exit quality, runtime writer behavior,
testnet readiness, or live readiness.

This is a docs-only review. It does not create fixture files, tests,
`runtime/order_intents/`, an `OrderIntentWriter`, adapters, private API access,
credentials, account reads, orders, testnet, live trading, or a VM observation.

## Evidence Reviewed

### Completed Observations

| Observation | Signal | Response | Risk and data | Paper state |
| --- | --- | --- | --- | --- |
| 24h | `WAIT=7` | `WATCH=7`, `PAPER_LONG=0` | `stale_data_count=0` | Closed and consistent |
| Prior 72h | `WAIT=19` | `WATCH=19`, `PAPER_LONG=0` | `HIGH=19`, `stale_data_count=0` | Closed and consistent |
| Latest 72h | `WAIT=18` | `WATCH=18`, `PAPER_LONG=0` | `MEDIUM=16`, `HIGH=2`, `weekly_daily_regime_mismatch=18`, `extreme_distance_from_ema50=2`, refresh `19/19/0`, `stale_data_count=0` | Closed and consistent |

The observations establish stable paper-only operation. They do not include an
observed Long1 activation, `PAPER_LONG`, paper-position transition,
duplicate-position rejection, exit, or invalidation.

### Design And Safety Artifacts

The review also considered:

- [BTC Long1 And PAPER_LONG Fixture Planning](btc_long1_paper_long_fixture_planning.md)
- [BTC Intent-Worthy Scenario Checklist](btc_intent_worthy_scenario_checklist.md)
- [BTC OrderIntentWriter Decision Memo](btc_order_intent_writer_decision_memo.md)
- [BTC OrderIntentWriter Design Proposal](btc_order_intent_writer_design_proposal.md)
- [BTC Order Intent Design](btc_order_intent_design.md)
- `schemas/btc_order_intent.schema.json`
- Existing inline schema, schema-audit, and writer-review tests.

The current schema already constrains `execution_allowed=false`, requires
`operator_review_required=true`, rejects unknown and credential-like fields,
rejects `testnet` and `live`, and requires `NONE` for response `BLOCK`, risk
`BLOCK`, and `stale_data`.

Existing tests exercise those core schema constraints with in-code payloads.
The writer review also lists future fixture requirements. This means standalone
fixture files would improve maintainability and scenario readability later,
but are not required to establish the current non-executing schema boundary.

## Benefits Of Adding Fixtures Later

After explicit approval, small test-only fixtures could make the following
behavior easier to review and regress:

- Schema rejection behavior.
- Credential-field rejection.
- `live` and `testnet` mode rejection.
- `stale_data` forcing no intent.
- Response `BLOCK` forcing no intent.
- Risk `BLOCK` forcing no intent.
- Malformed input rejection.
- Duplicate-position rejection.
- Paper-state consistency gates.
- Deterministic checksum expectations after checksum generation is separately
  implemented and approved.

Fixtures could also provide a stable shared vocabulary between schema tests,
future review-only validation, and the design-only writer proposal.

## Limits Of Fixtures

Fixture files are not market evidence.

They do not:

- Prove profitability or positive expectancy.
- Prove a Long1 edge.
- Prove entry or exit quality.
- Prove that `PAPER_LONG` occurred.
- Prove paper-position transition behavior unless based on a complete observed
  evidence packet.
- Validate an `OrderIntentWriter` runtime that does not exist.
- Justify runtime writer implementation by themselves.
- Justify adapters, private APIs, credentials, account access, testnet, or live
  trading.
- Permit strategy threshold changes or optimization.

A synthetic fixture can validate a specified safety rule. It cannot replace an
observed market event.

## Why Adding Fixture Files Now Is Premature

Adding fixture files now is premature because:

- `PAPER_LONG=0` across all completed observations.
- No observed entry transition exists.
- No actual paper-position transition exists.
- No observed duplicate-position, invalidation, or exit case exists.
- No runtime writer exists to consume or produce the proposed record shape.
- Existing inline tests already cover the core schema rejection boundary.
- No explicit approval has been given to create fixture files or new tests.
- Adding synthetic files now could look like implementation progress while
  adding no new market evidence.

The missing evidence is not another JSON example. It is an observed
intent-worthy event or explicit approval for a narrowly defined schema-only
synthetic test set.

## Smallest Acceptable Scope If Approved Later

Any later fixture task must be separately approved and limited to:

- `docs/examples/` or `tests/fixtures/` only.
- Clearly marked `observed` or `synthetic`.
- Synthetic status repeated inside the fixture or adjacent fixture manifest.
- Schema-only or review-only validation.
- No path under `runtime/`.
- No `runtime/order_intents/`.
- No writer runtime.
- No private API fields.
- No real or placeholder-shaped secrets that could be mistaken for
  credentials.
- No exchange account, balance, position, fill, or private order fields.
- No `live` or `testnet` accepted mode.
- No executable order path.
- No strategy threshold or parameter changes.
- Explicit approval of the exact filenames and tests before creation.

Negative schema fixtures may contain obvious invalid marker values solely to
prove rejection. They must never contain real credentials or be accepted as
valid records.

## Candidate Fixture Set For Later Approval

These are proposed filenames only. They are not created by this review.

| Candidate | Purpose | Evidence class | Expected allowed decision | Expected forbidden decision | Required safety assertions |
| --- | --- | --- | --- | --- | --- |
| `wait_watch_medium_risk.json` | Represent the common non-entry state with explained medium risk. | Observed if derived from one complete run/cycle packet; otherwise synthetic. | `NO_ACTION`, `CONTINUE_OBSERVATION`, `PAUSE_AND_REVIEW`. | `PAPER_LONG`, `IMPLEMENT_WRITER`, order placement. | Fresh completed candle; coherent paper state; `execution_allowed=false`; operator review; no intent write. |
| `wait_watch_high_risk.json` | Verify that high risk is not treated as readiness. | Observed if derived from one complete packet; otherwise synthetic. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | `PAPER_LONG`, risk suppression, writer implementation. | All risk flags preserved; no manual promotion; no state transition. |
| `stale_data_rejection.json` | Verify that stale data forces no intent. | Synthetic unless a complete observed stale case is approved. | `NO_ACTION`, `PAUSE_AND_REVIEW`, `DESIGN_ONLY_FIXTURE_CANDIDATE`. | Any long intent, forward-fill, order placement. | `stale_data` present; intended action `NONE`; no partial/future candle use. |
| `risk_block_rejection.json` | Verify that risk `BLOCK` dominates signal state. | Synthetic unless an observed block packet exists. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | Any intent path or risk override. | Risk `BLOCK`; intended action `NONE`; paper state unchanged. |
| `malformed_payload_rejection.json` | Verify fail-closed handling of missing or malformed required fields. | Synthetic negative fixture. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | Defaulting invalid values into a valid record. | Schema validation fails; no guessed fields; no runtime output. |
| `credential_field_rejection.json` | Verify rejection of credential-like fields. | Synthetic negative fixture. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | Credential storage, private API use, accepted record. | Obvious fake marker only; schema rejects unknown credential field; no secret. |
| `testnet_live_mode_rejection.json` | Verify rejection of prohibited modes. | Synthetic negative fixture. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | `START_TESTNET`, `START_LIVE`, accepted record. | Current mode enum remains closed; execution remains false. |
| `paper_state_inconsistent_rejection.json` | Verify that contradictory paper state cannot produce intent. | Synthetic unless an observed malformed state is approved. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | Silent repair, `PAPER_LONG`, state mutation. | Inconsistency explicit; fail closed; no inferred position fields. |
| `duplicate_position_rejection.json` | Verify that an existing open paper position blocks another long path. | Synthetic unless an observed duplicate-risk packet exists. | `NO_ACTION`, `PAUSE_AND_REVIEW`. | Second long, averaging down, duplicate intent. | One-position invariant; no second write; state unchanged. |
| `synthetic_paper_long_review_candidate.json` | Validate the review shape of a non-executing synthetic long candidate after explicit approval. | Synthetic only; never observed evidence. | `DESIGN_ONLY_FIXTURE_CANDIDATE`, `WRITER_PROPOSAL_REVIEW_CANDIDATE`. | Claiming observed `PAPER_LONG`, `IMPLEMENT_WRITER`, testnet/live, order placement. | Clearly synthetic; `operator_review_required=true`; `execution_allowed=false`; no adapter or runtime write. |

The synthetic paper-long candidate must not be named or described as an
observed `PAPER_LONG` event.

## Recommended Decision

Decision: `DO_NOT_ADD_FIXTURE_FILES_YET`.

- Keep fixture addition blocked until explicit approval.
- Keep the VM observation paused and the VM stopped.
- Wait for an observed intent-worthy case; or
- Ask for explicit approval to add a minimal schema-only synthetic fixture set.
- Keep runtime writer implementation, adapters, testnet, live trading, and
  order placement blocked.

The most defensible first synthetic set, if separately approved, would be only
negative schema/safety cases. An observed or synthetic paper-long review
candidate should require a separate scope decision because it is easier to
misinterpret as trading evidence.

## Go/No-Go Criteria

### GO For Fixture Files

Fixture files may be added only when:

- Explicit approval names the scope or exact files.
- Scope is limited to schema and safety validation.
- Files are stored only in an approved test-only or documentation-example
  path.
- No runtime files are created.
- No writer runtime is added.
- Every fixture is marked observed or synthetic.
- Tests cannot place orders, use adapters, call private APIs, read account
  state, or access credentials.
- The schema audit remains `PASS`.
- The writer design review remains `PASS`.
- Strategy thresholds and parameters remain unchanged.

GO for fixtures does not mean GO for a writer.

### NO-GO

Fixture addition is prohibited when:

- A fixture implies trading, implementation, testnet, or live readiness.
- A fixture is stored under `runtime/`.
- A fixture creates `runtime/order_intents/`.
- A fixture requires private API access, credentials, or exchange account
  state.
- A fixture accepts `live` or `testnet` mode.
- A fixture changes strategy thresholds or parameters.
- A fixture supports profitability or performance claims.
- A synthetic fixture is presented as observed market evidence.
- Operator review, schema audit, or writer-review gates are bypassed.

## Safety Boundary

- No `OrderIntentWriter` implementation.
- No `runtime/order_intents/`.
- No runtime fixture files.
- No adapters.
- No private API.
- No API keys or credentials.
- No account reads.
- No order placement, cancellation, amendment, or reconciliation.
- No testnet or live trading.
- No strategy threshold changes.
- No optimization.
- No profitability claims.
- No VM restart.

## Suggested Next Codex Prompt

> Ask for explicit approval before adding a minimal schema-only synthetic
> fixture set for BTC safety validation.

## Implementation Readiness

Implementation readiness: none.

This review does not make the project fixture-approved, writer-ready,
testnet-ready, or live-ready.
