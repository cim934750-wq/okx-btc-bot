# Exact-Instrument OI Audit Postmortem Round 1

## Scope

This is a research-only postmortem and synthesis for `exact_instrument_oi_audit_round1`. It does not fetch OI data, run backtests, run validation, define a trading strategy, tune parameters, change source code, change production parameters, modify PRs, restart dry-run, create live-trading plans, or claim implementation readiness.

## Context

The prior OHLCV-only strategy path failed, Candidate D failed fetched later-data validation, and the funding-gated Candidate D path reduced losses but failed to create positive expectancy. The exact-instrument OI audit was run to answer a narrower data-quality question before any OI strategy could be considered.

The audit covered the same 19 OKX USDT swap instruments. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible. Current exact OI was available for 19/19 instruments, while historical OI-like data was available for 19/19 through a currency-level route. The audit decision was `usable_only_as_aggregate_context`.

## Main Finding

Exact current instrument OI is not the same thing as exact historical instrument OI.

The current OKX endpoint `/api/v5/public/open-interest` returns exact instrument snapshots with `instId`, `oi`, `oiCcy`, `oiUsd`, and timestamp fields. That is useful for current unit checks and endpoint provenance, but it is only a snapshot. It cannot support historical 4h validation because it does not provide a time series over prior reference, holdout, or later-data windows.

The historical route `/api/v5/rubik/stat/contracts/open-interest-volume` returns 1h OI-like value/volume arrays by currency. The response does not include `instId`, and adding `instId` did not prove that the route becomes exact-instrument history. Therefore the historical route cannot be treated as exact historical instrument-level OI.

ccxt `fetch_open_interest_history` did not resolve this limitation. It provided historical OI-like data but did not prove exact historical instrument identity beyond the underlying OKX public route.

## Exact Current Versus Aggregate Historical

The audit distinguishes three concepts:

1. Exact current instrument snapshot: a point-in-time exact OKX swap instrument OI payload. Usable for unit checks only.
2. Historical aggregate or ccy-level context: a historical OI-like series tied to the base currency or broader contracts context. It may be timestamped and alignable, but it is not instrument-level proof.
3. Exact historical instrument-level feature: a timestamped history for the exact swap instrument with stable, auditable units. This is required before any exact-instrument OI strategy definition.

Only the first two were observed. The third was not proven.

## Why No Exact-Instrument OI Strategy Should Be Defined

An OI entry/exit strategy would require a historical feature stream that is instrument-specific, unit-consistent, and alignable to 4h candles without leakage. The available historical route does not meet that standard. Treating the ccy-level route as exact instrument OI would blur provenance, overstate precision, and risk building rules on a feature that may not correspond to the traded instrument.

Because current exact OI is only a snapshot, it also cannot be used for historical validation. A strategy cannot be validated from current snapshots plus aggregate historical context without changing the research claim.

## Decision

Decision: `stop_oi_research_keep_benchmark_only` as the conservative default.

Optional research-only continuation: `plan_aggregate_context_only_audit`, but only if explicitly approved and constrained so aggregate OI is never described as exact instrument OI. External vendor exact-OI history audit is also possible only if explicitly approved, with provenance and licensing constraints.

## Aggregate-Context-Only Constraints

If aggregate-context-only research is pursued later:

- It cannot be treated as an instrument-level signal.
- It can only be used as market-wide or base-currency context.
- It must not decide entries or exits alone.
- It must be validated separately as a context feature only.
- It must not be mixed with exact OI claims.
- BTCUSDT, DOGEUSDT, DOTUSDT, UNIUSDT, and the same 19-market universe must remain visible.
- No dry-run, live, or implementation-readiness claim may follow directly from aggregate-context audit work.

## Closed Items

The following are closed from the current OKX/ccxt historical route:

- Exact-instrument OI strategy definition.
- OI-based entry/exit strategy definition from the current data route.
- Treating ccy-level historical OI as exact instrument OI.
- Dry-run/live planning.
- Implementation readiness.

## Allowed Next Steps

Allowed research-only next steps are conservative:

- Keep no-trade / capital preservation as default.
- Continue benchmark-only monitoring.
- Create an aggregate-context-only audit plan with strict constraints, if explicitly approved.
- Audit an external vendor exact historical OI source, if explicitly approved.
- Create a fresh feature inventory only if a genuinely new data source appears.

## Recommendation

Do not define an OI strategy from the current OKX/ccxt historical route. The clean default is to stop OI strategy research and keep benchmark/no-trade mode. If research continues, the next step should be a plan-only aggregate-context audit or an explicitly approved external exact-OI vendor audit, not validation or trading.
