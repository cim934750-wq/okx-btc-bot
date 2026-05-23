# Exact-Instrument Open-Interest Audit Plan Round 1

## Scope

This is a research-only audit-design memo. It does not fetch open-interest data, run backtests, run validation, define a trading strategy, tune parameters, change source code, change production parameters, modify PRs, restart dry-run, create live-trading plans, or claim implementation readiness.

## Background

The OHLCV-only research path failed across the long-only chain, Candidate D later-data validation, and the autonomous OHLCV-only discovery loop. Funding-first research was then tested through `funding_extreme_avoidance_filter_round1`. That filter reduced Candidate D later-data losses from -174.23 to -126.24, but it still failed: PF was 0.0000, win rate was 0.00%, BTCUSDT remained negative, and no-trade remained preferred.

Funding therefore remains a potentially useful feature class, but the frozen funding-gated Candidate D path is closed. The prior OI/funding data availability audit found funding history broadly available across 19/19 markets, while historical open interest was only partially usable: the available historical route appeared constrained as 1h/base-currency aggregate history, not clearly exact OKX swap instrument history. Current exact instrument OI was available only for unit checks.

## Why A Deeper OI Audit Is Needed

Open interest could represent a distinct feature class from OHLCV and funding because it may capture positioning expansion, contraction, crowding, or squeeze risk. But it cannot be used responsibly until the data provenance and units are clear. The next question is not whether an OI strategy works; the question is whether exact-instrument historical OI exists for the same 19 OKX swap instruments and can be aligned to 4h research candles without leakage.

## Exact OI Audit Objective

The audit should answer:

Can we obtain historical open interest for the exact OKX swap instrument for each of the same 19 markets, with timestamped, unit-consistent values that are alignable to 4h OHLCV candles without future leakage?

The audit must preserve BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visibility. It must not remove markets after observing coverage or quality.

## Instruments

The planned instrument map uses the same 19 markets from prior OHLCV validation and maps spot-style symbols to OKX USDT swap instrument IDs, for example BTCUSDT to BTC-USDT-SWAP. The full mapping is in `exact_instrument_oi_audit_plan_round1_instrument_mapping.csv`.

## Data Sources To Audit Later

A future approved audit may compare:

- OKX native public REST endpoints, including current exact-instrument OI endpoints and any historical/trading-data OI endpoints that can be proven exact-instrument rather than aggregate.
- ccxt methods, if they expose exact instrument historical OI with timestamp and unit metadata.
- Existing local raw audit data as a prior baseline and provenance check.
- Third-party vendors only as a future optional source, not as part of this plan unless explicitly approved later.

No data is fetched in this plan.

## Required Data Properties

For each instrument and timestamp, the future audit must capture timestamp, instrument ID, open interest value, unit/currency/contract denomination, source endpoint, fetch timestamp, and raw response archive or hash. Unit checks must determine whether values are contract count, base currency, quote notional, or another exchange-specific representation.

## Coverage And Alignment Requirements

Coverage must be assessed across all 19 markets. The target is enough history to overlap prior OHLCV reference, holdout, and later-data windows. Each dataset must report start/end timestamps, row counts, sampling intervals, gaps, duplicates, timezone consistency, and whether 4h alignment can be done using same/prior OI observations only.

No forward-looking OI may be used. If OI is sampled more frequently than 4h, the audit should document how to choose the last known observation at or before each 4h candle. If OI is sampled less frequently than 4h or has gaps, the audit must define staleness and missing-data reporting before any strategy plan.

## Usability Decision Classes

The future audit should classify each market and the overall dataset as one of:

- `usable_exact_instrument_oi`.
- `partially_usable_exact_but_short_history`.
- `usable_only_as_aggregate_context`.
- `not_usable_for_strategy_research`.

A strategy definition is not allowed unless the audit supports exact-instrument usability or explicitly constrained partial usability.

## Possible Future Strategy Classes If Usable

Only if exact OI history is usable, future research could define a separate frozen plan for OI expansion breakout, price/OI divergence, crowded-position avoidance, OI contraction exhaustion, or squeeze-risk regime classification. None of those are defined or validated here.

## Recommendation

Execute the exact-instrument OI audit only after explicit approval. Do not define an OI strategy until the audit proves whether exact historical OI is available, unit-consistent, and alignable to the research windows. Until then, no-trade remains the default and implementation readiness remains closed.
