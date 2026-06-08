# BTC OrderIntentWriter Design Proposal

## Purpose

This proposal defines a future non-executing `OrderIntentWriter` boundary for the BTC paper-mode MVP. The writer would eventually convert local paper-mode signal, risk, response, and paper-state evidence into append-only JSON review records that describe what the paper system would have wanted to review.

The writer must stay non-executing. It must not place, cancel, amend, reconcile, or route orders. It must not call exchange APIs, read accounts, use credentials, add adapters, enable testnet, or enable live trading.

Current implementation remains premature because documented 24h and 72h VM observations produced `PAPER_LONG=0`. No observed market state has yet validated paper entry, exit, duplicate-position blocking, invalidation, or paper-state transition behavior. A writer implemented now would mostly record `NONE` or `WATCH_ONLY` records and would not prove the more important intent paths.

This document is design-only. It does not implement the writer, create `runtime/order_intents/`, add fixture files, add tests, add adapters, or change strategy behavior.

## Source Inputs

A future writer may read only existing paper-mode artifacts and in-memory outputs:

- signal decision output from the deterministic BTC Long1 signal engine,
- risk assessment output from the risk engine,
- response action output from the response engine,
- paper state snapshot from `runtime/paper_state.json`,
- latest completed candle metadata,
- stale-data status and latest candle freshness metadata,
- local decision log metadata,
- paper status dashboard snapshot metadata,
- daily review, alert summary, and operator checklist status,
- schema version from `schemas/btc_order_intent.schema.json`,
- observation/run metadata such as run timestamp, cycle identifier, command source, and local source paths.

The writer should not infer missing fields. If a required paper-mode input is missing, malformed, or internally inconsistent, the writer design must fail closed and write no runtime intent.

## Explicit Non-Inputs

A future writer must not read or depend on:

- API keys,
- exchange secrets or passphrases,
- exchange account state,
- balances,
- positions,
- fills,
- private exchange endpoints,
- order books from private or authenticated APIs,
- adapters,
- testnet configuration,
- live configuration,
- account identifiers,
- withdrawal permissions,
- environment variables containing credentials.

Credential presence must never change writer behavior. Unknown private or adapter input should be treated as a safety violation, not as optional context.

## Append-Only Runtime Path Rules

This section is design-only. The path must not be created by this task.

Future path pattern:

```text
runtime/order_intents/YYYYMMDD/<timestamp>_<symbol>_<decision_id>.json
```

Required path rules:

- append-only writes,
- no overwrite,
- no mutation after write,
- no deletion by the writer,
- no symlink targets,
- deterministic filename derived from UTC timestamp, symbol, and decision identifier,
- reject duplicate `decision_id` for the same symbol and candle timestamp,
- reject stale data,
- reject response `BLOCK`,
- reject risk level `BLOCK`,
- reject malformed or inconsistent paper state,
- reject duplicate open paper position when generating a long-review record,
- write through an atomic temporary file in the same directory and then rename,
- fsync the file before rename,
- fsync the parent directory after rename,
- use restrictive local file permissions,
- keep runtime intent files out of commits unless explicitly approved as small fixtures.

The writer must never create a best-effort partial file. If atomic write preparation fails, no intent should be considered written.

## Intent Action Rules

Writer-level review action vocabulary:

| Writer review action | Meaning | Executing? |
| --- | --- | --- |
| `NONE` | No intent-worthy action should be recorded. Required for blocked, stale, malformed, or no-action states. | no |
| `WATCH_ONLY` | Record that the system stayed in observation mode with non-blocking evidence. | no |
| `PAPER_LONG_REVIEW` | Record a future operator-review candidate for a paper long event. | no |
| `EXIT_REVIEW` | Record a future operator-review candidate for paper exit or invalidation review. | no |

No action may mean exchange execution. No action may place, cancel, amend, or modify orders. Any future `PAPER_LONG_REVIEW` or `EXIT_REVIEW` must require operator review.

Current schema alignment:

- `NONE` maps to schema `intended_action=NONE`.
- `WATCH_ONLY` maps to schema `intended_action=WATCH_ONLY`.
- `PAPER_LONG_REVIEW` maps to current schema `intended_action=PAPER_LONG_INTENT` with `operator_review_required=true` and `execution_allowed=false`.
- `EXIT_REVIEW` maps to current schema `intended_action=PAPER_EXIT_INTENT` with `operator_review_required=true` and `execution_allowed=false`.

If a future implementation wants the literal schema values `PAPER_LONG_REVIEW` or `EXIT_REVIEW`, the schema must be changed in a separate approved schema task before runtime writer implementation.

Required action rules:

- `stale_data` forces `NONE`.
- Response `BLOCK` forces `NONE`.
- Risk level `BLOCK` forces `NONE`.
- Missing or malformed paper state forces no write, or `NONE` only if a future design explicitly chooses to record blocked review records.
- Duplicate open paper position blocks `PAPER_LONG_REVIEW`.
- Unresolved risk flags require a block reason or a reviewed `WATCH_ONLY` outcome.

## Schema Validation

The future writer must validate every candidate record against:

```text
schemas/btc_order_intent.schema.json
```

Required schema constraints:

- `execution_allowed=false`,
- `operator_review_required=true`,
- `mode` limited to `paper`, `order_intent_only`, or `simulated_dry_run`,
- `testnet` and `live` rejected,
- credential-like fields rejected,
- `additionalProperties=false`,
- response `BLOCK` forces `intended_action=NONE`,
- risk level `BLOCK` forces `intended_action=NONE`,
- `stale_data` in `risk_flags` forces `intended_action=NONE`,
- non-negative quantity, notional, and max-notional fields,
- valid UTC timestamp formats,
- non-empty `execution_blocked_reason`.

Schema validation must run before any future file write. Validation failure must produce no runtime intent file.

## Checksum Behavior

Checksum behavior is design-only.

Future checksum rules:

- Build canonical JSON using sorted keys, stable separators, UTF-8 encoding, and no volatile formatting.
- Exclude `checksum_or_hash` from the payload before hashing.
- Use SHA-256 over the canonical payload.
- Store the hex digest in `checksum_or_hash`, or use a prefixed form such as `sha256:<hex>`.
- Optionally include a future `previous_intent_hash` only after a separate schema update and approval.
- A future checksum verification CLI may read records and recompute hashes.
- Checksum mismatch must mark the record invalid or blocked for review.
- Checksum mismatch must never be auto-fixed by the writer.
- Checksum logic must never include credentials, account identifiers, or private API fields.

Any append-only chain design must remain local and non-executing. A hash chain cannot authorize execution.

## Fixture Test Proposal

These are future fixture test requirements only. This task does not add tests or fixture files.

Future tests should cover:

- `WAIT` or `WATCH` with risk `HIGH` emits `WATCH_ONLY` or `NONE` only,
- clean `PAPER_LONG` evidence emits `PAPER_LONG_REVIEW` mapped to a non-executing schema value,
- `stale_data` emits or validates only `NONE`,
- response `BLOCK` emits or validates only `NONE`,
- risk level `BLOCK` emits or validates only `NONE`,
- inconsistent paper state rejects the candidate or writes no record,
- duplicate `decision_id` rejects a second write,
- duplicate open paper position blocks a long-review candidate,
- private key or credential-like fields are rejected,
- `live` and `testnet` modes are rejected,
- checksum generation is deterministic,
- checksum mismatch is invalid and not auto-fixed,
- malformed payloads are rejected,
- missing source decision log path or snapshot path blocks the candidate unless a future approved policy allows a null source with explicit block reason,
- atomic temp-file failure leaves no visible intent file.

The tests should use small local fixtures only. They must not call external APIs, read credentials, create real orders, create adapters, or require exchange accounts.

## Safety Gates

A future writer must apply these gates before schema validation and before any file write:

1. Paper-only gate: current mode must be paper-safe.
2. Stale-data gate: active `stale_data`, missing candle timestamp, or incomplete candle blocks intent creation.
3. Risk `BLOCK` gate: risk level `BLOCK` forces `NONE` or no write.
4. Response `BLOCK` gate: response action `BLOCK` forces `NONE` or no write.
5. Paper state consistency gate: malformed, missing, or contradictory paper state blocks intent creation.
6. Duplicate prevention gate: duplicate decision identity, duplicate candle identity, or duplicate open long state blocks long-review records.
7. Schema validation gate: candidate must validate against the current non-executing schema.
8. Operator review gate: `operator_review_required` must be `true`.
9. Execution-disabled gate: `execution_allowed` must be `false`.
10. No-private-API gate: no private endpoint, account, balance, position, fill, key, or credential field may be present.
11. No-adapter gate: writer must not instantiate, import, or call an exchange adapter.
12. No-testnet/live gate: `testnet` and `live` modes remain rejected.
13. Checksum gate: canonical checksum must be deterministic before the record is considered valid.

Any unknown gate result must fail closed.

## Readiness Status

Current status:

- proposal only,
- no runtime writer,
- no `runtime/order_intents/`,
- no adapter,
- no simulated adapter,
- no testnet or live trading,
- no private API or API key access,
- not implementation-ready while `PAPER_LONG=0` and no clear intent-worthy scenario exists,
- not profitability evidence,
- not testnet readiness,
- not live readiness.

## Future Implementation Prerequisites

Runtime implementation can be considered only after:

- explicit user approval,
- at least one explainable `PAPER_LONG` or clear intent-worthy event,
- continued multi-day paper stability,
- `stale_data` and expected-WARN behavior remain explainable,
- schema audit remains `PASS`,
- writer review remains `PASS`,
- paper-state transition behavior is understood,
- clear no-go behavior exists for stale data, response `BLOCK`, risk `BLOCK`, malformed state, and duplicate paper position,
- fixture tests are specified and approved,
- the team agrees whether to use current schema values (`PAPER_LONG_INTENT`, `PAPER_EXIT_INTENT`) or update the schema to literal review labels.

## Non-Goals

- No Python writer implementation.
- No runtime intent directory creation.
- No runtime intent files.
- No fixture files in this task.
- No exchange adapter.
- No simulated adapter.
- No private API.
- No API keys.
- No account balance reads.
- No order placement.
- No testnet trading.
- No live trading.
- No strategy parameter changes.
- No threshold optimization.
- No profitability or readiness claim.

## Decision

The proposal is safe to keep as a design artifact. Runtime `OrderIntentWriter` implementation remains blocked until explicit approval and stronger paper evidence, especially an explainable `PAPER_LONG` or other clearly intent-worthy scenario.
