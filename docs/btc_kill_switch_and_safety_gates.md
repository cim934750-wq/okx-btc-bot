# BTC Kill Switch And Safety Gate Design

## Purpose

This document defines future kill-switch, safety-gate, and API-key safety requirements for any possible order-intent, simulated dry-run, or testnet transition. It is design-only and does not implement trading, private API access, or exchange orders.

## Default Safety Rule

All future execution-capable components must fail closed. If a gate cannot prove that action is allowed, action is blocked.

## Required Kill Switches

### Local Kill Switch File

- A local file path, for example `runtime/KILL_SWITCH`, should immediately block order-intent execution and all future adapter actions.
- Presence of the file should be enough to block action.
- The file should not need network access or credentials.

### Environment Kill Switch

- An environment variable, for example `BTC_BOT_KILL_SWITCH=1`, should block all future adapter actions.
- This must override any runtime mode setting.

### Stale-Data Kill Switch

- Active `stale_data` must block action.
- Missing latest candle timestamp must block action.
- Incomplete latest candle must block action.

### Repeated-Error Kill Switch

- Repeated validation, adapter, API, or reconciliation errors must block action.
- The error threshold must be conservative and documented before implementation.

### Max Daily Loss Kill Switch

- A future simulated/testnet daily loss limit must block additional actions.
- The current MVP does not calculate or enforce real PnL.

### Max Drawdown Kill Switch

- A future paper/testnet drawdown limit must block additional actions.
- Drawdown calculation must be auditable and based on explicit paper/testnet state.

### Duplicate-Order Kill Switch

- Duplicate open paper position, duplicate unresolved order intent, or duplicate active testnet order must block new action.
- Duplicate detection must use symbol, side, candle timestamp, and source decision identity.

### Position-Reconciliation Failure Kill Switch

- Future testnet reconciliation failure must block action.
- Reconciliation must prove expected orders, fills, cancels, and local state agree before more action is allowed.

### Manual Operator Stop

- Any manual operator stop must block action until a separate manual review clears it.
- A manual stop should never be auto-cleared by a signal, adapter, or loop.

## Required Pre-Order Safety Gates

These gates are required before any future testnet order can be considered. The current MVP does not execute them against an exchange.

1. Data freshness check.
2. Latest candle completeness check.
3. Signal decision check.
4. Response action check.
5. Risk level check.
6. Risk flag check.
7. Paper state consistency check.
8. Duplicate intent check.
9. Max notional check.
10. Max order frequency check.
11. Account mode check.
12. Adapter mode check.
13. API key permission check.
14. Operator approval checkpoint.

## Gate Rules

- `response_action=BLOCK` blocks action.
- `risk_level=BLOCK` blocks action.
- `stale_data` blocks action.
- Missing or malformed paper state blocks action.
- Duplicate open paper position blocks action.
- Unresolved risk flags block action unless a future approved whitelist exists.
- Unknown adapter mode blocks action.
- Missing operator approval blocks testnet and live action.
- Live action remains forbidden by this design.

## API Key Safety Requirements

- No keys committed.
- No keys in config files.
- No keys in logs.
- No keys in docs examples.
- Environment-variable loading only.
- Testnet and live keys must be separate.
- Withdrawal permission must be disabled.
- IP whitelist is recommended.
- Read/write permissions must be separated.
- Secret scanning is required before any future private API code.
- Key rotation procedure is required before any future testnet adapter use.
- Emergency revoke procedure is required before any future testnet adapter use.
- API keys must never be printed, serialized into order intents, or included in exception output.
- Adapter code must redact request headers, signatures, passphrases, and account identifiers.

## Operator Approval Checkpoint

Any future transition beyond paper reporting must require an explicit operator approval record that includes:

- approved mode,
- approved symbol/instrument,
- max notional cap,
- time window,
- allowed adapter,
- reviewed kill-switch state,
- reviewed API-key safety checklist,
- reviewed latest paper status,
- acknowledgement that live trading remains disabled unless separately approved.

## Failure Handling

When any gate fails:

- return or record a blocked state,
- include the failed gate name,
- include the source decision/snapshot path when available,
- do not retry automatically unless the future design explicitly allows safe local retry,
- do not call private APIs,
- do not place or cancel orders,
- require manual review for repeated failures.

## Non-Goals

- No kill-switch implementation is added in this task.
- No order execution is added in this task.
- No private API access is added in this task.
- No account or balance access is added in this task.
- No live-trading readiness is claimed.
