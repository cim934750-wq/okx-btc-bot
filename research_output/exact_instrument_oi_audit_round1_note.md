# Exact-Instrument OI Data Availability Audit Round 1

## Scope

This is a research-only data availability audit. Public OKX open-interest data was fetched only to assess whether exact OKX swap historical OI exists for the same 19 markets and whether it is unit-consistent, timestamped, and alignable to 4h research candles. No trading strategy was defined or tested, no OHLCV was fetched, no backtest or validation was run, and no production source, parameter, deployment, dry-run, or live behavior was changed.

## Instruments Audited

The audit used the same 19 mapped OKX USDT swap instruments from the plan. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible in all summary tables.

## Data Sources Checked

- Native OKX current exact open-interest endpoint: `/api/v5/public/open-interest` with `instType=SWAP` and exact `instId`.
- Native OKX historical contracts OI/volume endpoint: `/api/v5/rubik/stat/contracts/open-interest-volume` with `ccy=<base>` and `period=1H`.
- Native historical endpoint with `ccy=<base>` plus `instId=<instrument>` to test whether exact instrument identity is honored.
- ccxt OKX `fetch_open_interest_history(symbol, timeframe=1h, limit=100)` for comparison.
- Existing previous audit raw files were inspected as provenance/context only.

Raw fetched payloads were saved under `research_output/exact_instrument_oi_audit_round1_raw/`.

## Availability Summary

Current exact instrument OI is available for 19/19 markets through the native current endpoint. The current payload includes exact `instId`, `instType`, `oi`, `oiCcy`, `oiUsd`, and timestamp fields.

Historical OI-like data is available for 19/19 markets at 1h cadence through the Rubik contracts OI/volume endpoint, but this route is currency-based. The response rows are arrays of timestamp, OI value, and volume, and they do not include `instId`. Adding `instId` while retaining `ccy` produced the same currency-route payload in this audit, so exact-instrument historical OI was not proven.

## Unit Consistency

The current exact endpoint exposes contract/base/USD fields that are suitable for current unit checks. The historical route does not expose exact instrument identity or equivalent `oi`, `oiCcy`, and `oiUsd` fields. It is therefore not safe to reconcile the historical route as exact instrument history, nor to perform cross-market exact OI comparisons without additional source support.

## 4h Alignment

The historical ccy route is 1h timestamped data and can technically be aligned to 4h candles using same/prior timestamps without forward leakage if treated only as aggregate context. However, because exact instrument history is not proven, it should not be used as exact-instrument OI for strategy research. Current exact OI is only a snapshot and cannot support historical 4h validation.

## Gaps And Duplicates

The fetched historical ccy-route samples were assessed for row count, modal interval, gaps, duplicate timestamps, and UTC timestamp consistency. See `exact_instrument_oi_audit_round1_gaps_duplicates.csv` for per-market details.

## Usability Decision

Overall classification: `usable_only_as_aggregate_context`.

This means exact current OI is available for unit checks, and 1h historical OI-like data is available as currency-level context, but exact-instrument historical OI was not established through the audited OKX/ccxt public route. No exact-instrument OI strategy research should be defined from this route alone.

## Recommendation

Do not define or validate an OI strategy from this route. If OI research continues, either find an explicitly exact-instrument historical source with unit metadata or create a separate aggregate-context research plan that clearly states it is not exact instrument OI. No-trade remains the default and implementation readiness remains closed.
