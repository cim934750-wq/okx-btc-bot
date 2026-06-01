# BTC Order Intent Design

## Purpose

An order intent is a non-executing, auditable record of what the paper system would have wanted to do after a deterministic signal, risk, and response decision.

This design does not implement order writing, exchange access, testnet trading, or live trading. It defines a future record boundary only.

The current non-executing schema lives at `schemas/btc_order_intent.schema.json`. It validates record shape and safety constraints only; it does not create order intents, call an exchange, or trade.

## Design Boundary

- Order intents are paper/testnet planning artifacts, not orders.
- The current MVP must not execute an intent.
- `execution_allowed` defaults to `false`.
- No intent may contain API keys, secrets, credentials, session tokens, account identifiers, or withdrawal data.
- No intent may call an exchange, place an order, cancel an order, or query private account state.
- Intent storage must be append-only and auditable.
- Any future implementation must fail closed when required fields, source logs, paper state, or risk fields are missing.

## Proposed Record Fields

| Field | Required | Description |
| --- | --- | --- |
| `intent_id` | yes | Stable unique identifier for the intent record. |
| `created_at_utc` | yes | UTC timestamp when the intent was created. |
| `source` | yes | Source command or component, for example `btc_signal_response_mvp`. |
| `schema_version` | yes | Schema version. Current schema requires `1.0.0`. |
| `mode` | yes | `paper`, `order_intent_only`, or `simulated_dry_run`. Current schema rejects `testnet` and `live`. |
| `symbol` | yes | Human symbol, for example `BTCUSDT`. |
| `instrument_id` | yes | Exchange instrument identifier, for example `BTC-USDT`. |
| `timeframe` | yes | Source timeframe, for example `4h`. |
| `candle_timestamp` | yes | Latest completed candle timestamp used by the signal. |
| `signal_decision` | yes | Normalized signal decision: `WAIT`, `LONG1`, `NO_SIGNAL`, or `UNKNOWN`. |
| `response_action` | yes | Response engine action such as `WAIT`, `WATCH`, `PAPER_LONG`, `BLOCK`, or `EXIT_WARNING`. |
| `risk_level` | yes | Risk assessment level: `LOW`, `MEDIUM`, `HIGH`, `BLOCK`, or `UNKNOWN`. |
| `risk_flags` | yes | Ordered list of active risk flags. |
| `long1_active` | yes | Whether the Long1 starter signal is active. |
| `confidence` | yes | Signal confidence label from the deterministic engine. |
| `passed_conditions` | yes | Long1 conditions that passed. |
| `missing_conditions` | yes | Long1 conditions that did not pass. |
| `intended_action` | yes | `NONE`, `PAPER_LONG_INTENT`, `PAPER_EXIT_INTENT`, or `WATCH_ONLY`. |
| `intended_side` | yes | `NONE` or `LONG`. Shorts remain out of scope for the current MVP. |
| `intended_order_type` | yes | `NONE`, `MARKET_SIMULATION`, or `LIMIT_SIMULATION`. These labels do not place orders. |
| `intended_quantity` | yes | Future planning quantity. Current schema requires a non-negative number. |
| `intended_notional` | yes | Future planning notional. Current schema requires a non-negative number. |
| `max_notional_cap` | yes | Maximum allowed future planning notional. Current schema requires a non-negative number. |
| `stop_loss_reference` | yes | Future invalidation or stop reference. Current safe default is `null`. |
| `invalidation_reason` | yes | Reason this intent should be treated as invalid, if any. |
| `block_reason` | yes | Blocking reason when no executable future action may be considered. |
| `source_decision_log_path` | yes | Local source decision JSONL path or `null` if unavailable. |
| `source_snapshot_path` | yes | Local daily/status snapshot path or `null` if unavailable. |
| `operator_review_required` | yes | Must be `true` for current and future transition stages. |
| `execution_allowed` | yes | Must default to `false`; current design requires `false`. |
| `execution_blocked_reason` | yes | Explicit reason execution is disabled. |
| `checksum_or_hash` | yes | Hash over canonical intent fields for tamper detection. |
| `notes` | yes | Human-readable non-secret notes. |

## Required Rules

- `execution_allowed` must default to `false`.
- Any `BLOCK` response must produce no executable intent.
- Any `BLOCKED` signal decision must produce no executable intent.
- Any `stale_data` risk flag must block execution.
- Missing or malformed paper state must block execution.
- Duplicate open paper position state must block execution.
- Any unresolved risk flag must block execution unless a future design explicitly whitelists it with tests and manual approval.
- Missing source decision logs or snapshots must block execution.
- Missing latest candle timestamp must block execution.
- Missing paper state consistency check must block execution.
- Intent records must be append-only and immutable after write.
- Corrections must be represented by a new intent or invalidation record, not by editing history.
- Intent records must never contain API keys or credentials.
- Intent records must not place, cancel, amend, or reconcile orders.
- The current schema rejects unknown fields through `additionalProperties=false`.
- Credential-like fields such as `api_key`, `api_secret`, `secret`, `passphrase`, `password`, `token`, `access_token`, `refresh_token`, `private_key`, `exchange_api_key`, `exchange_api_secret`, `okx_api_key`, `okx_secret_key`, and `okx_passphrase` are not accepted.
- Current schema modes are limited to `paper`, `order_intent_only`, and `simulated_dry_run`; `testnet` and `live` are rejected.
- Current schema requires `operator_review_required=true`.

## Non-Executing Lifecycle

1. Read the latest deterministic signal, risk, response, monitoring, and paper-state snapshot.
2. Build a candidate order intent only from local paper-mode data.
3. Apply safety gates before the record is considered valid.
4. Set `execution_allowed=false`.
5. Set `operator_review_required=true`.
6. Write an append-only local intent record in a future approved path.
7. Include source paths and a checksum.
8. Require manual human review before any future testnet adapter can read it.

## Canonical Current Defaults

```json
{
  "schema_version": "1.0.0",
  "mode": "paper",
  "intended_action": "NONE",
  "intended_side": "NONE",
  "intended_order_type": "NONE",
  "intended_quantity": 0,
  "intended_notional": 0,
  "max_notional_cap": 0,
  "operator_review_required": true,
  "execution_allowed": false,
  "execution_blocked_reason": "current_mvp_is_paper_only"
}
```

## Schema Validation

Validate the schema tests with:

```bash
.venv-btc-signal-mvp/bin/python -m pytest tests/test_btc_order_intent_schema.py
```

The schema is intentionally non-executing. Passing validation means only that the JSON object has the expected review shape and safety constraints. It does not authorize order placement, private API calls, testnet use, or live trading.

## Audit Requirements

- Intent records must include source decision and snapshot paths.
- Intent records must include active risk flags and blocked reasons.
- Intent records must be sorted or canonically serialized before hashing.
- Intent records must be append-only.
- Intent paths must not be committed when they are runtime outputs.
- Runtime intent files, if added later, must stay under a local ignored runtime directory unless explicitly added as small fixtures.

## Non-Goals

- No live orders.
- No testnet orders.
- No exchange client.
- No private API calls.
- No account balance reads.
- No real position management.
- No external notifications.
- No strategy optimization.
- No profitability validation.
