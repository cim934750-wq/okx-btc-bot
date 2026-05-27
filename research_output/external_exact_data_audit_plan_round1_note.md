# External Exact-Data Audit Plan Round 1

## Purpose
This is a research-only plan for auditing external exact historical data sources for instrument-level taker flow, trades, open interest, basis, funding, and premium/index context. It does not fetch external data, call vendor APIs, scrape websites, validate strategies, run backtests, define candidates, tune thresholds, change production code, restart dry-run, create live plans, or claim implementation readiness.

## Why This Audit Is Next
External exact-data audit is the correct next research step because the current local/public routes did not prove the exact historical instrument-level data needed for strategy research.

- CP1 public-trade reconstruction failed under the 2,500-request cap: one BTC-USDT-SWAP 4h bucket could not be fully covered.
- CP1 reached only `2026-05-26T10:12:42.756Z` for the `2026-05-26T08:00:00Z` to `2026-05-26T12:00:00Z` bucket, leaving about 2h12m42.756s missing.
- The current OKX/ccxt exact historical OI route was not proven; current exact OI snapshots are not historical instrument-level OI time series.
- OKX Rubik taker-volume data was aggregate ccy/contracts context, not exact instrument-level taker flow.
- No strategy should be built on incomplete trade buckets, aggregate context mislabeled as exact instrument flow, or unproven OI/basis history.

## Audit Goal
The goal is to identify whether external APIs, vendors, datasets, or exchange-specific sources can provide exact historical instrument-level data with enough coverage, semantics, provenance, cost clarity, and licensing for future research.

The audit should answer, before any paid or broad fetch:

- Does the source support exact OKX swap/perp instruments such as BTC-USDT-SWAP and DOGE-USDT-SWAP?
- Does the source provide raw trades or direct taker buy/sell volume with clear taker/aggressor side semantics?
- Does the source provide exact historical instrument-level OI, not only exchange-wide or currency-level OI?
- Does the source provide basis, mark/index/last, funding, premium, or futures/perp spread context with data dictionary clarity?
- Can raw payloads be archived reproducibly with license permission for internal research?
- Can data align cleanly to existing UTC 4h OHLCV candles without leakage or forward-fill?

## Minimum Viable Data Contract
A source is useful only if it can provide a documented data contract. Required fields include instrument ID, timestamp, raw source provenance, and category-specific fields such as trade price/size/side, taker buy/sell volume, OI quantity/notional, funding rate, premium/index, mark/index/last price, and basis/spread definitions.

For trade-flow research, taker/aggressor side must be explicit and documented. If side semantics are ambiguous, the source cannot support exact taker-flow research.

For OI research, the OI field must be exact instrument-level history. Exchange-wide, base-currency, or aggregate contracts OI must be labeled as context only.

## Future Minimal Sample Audit
No sample audit is executed here. If explicitly approved later, the first external sample audit should be minimal:

1. Select one source that passes manual documentation/pricing review.
2. Audit BTC-USDT-SWAP first.
3. Add DOGE-USDT-SWAP only if BTC passes.
4. Use one completed UTC 4h bucket or one UTC day depending on source granularity.
5. Archive raw payloads, data dictionary, license note, pricing note, and reproducibility metadata.
6. Align sample rows to existing 4h OHLCV boundaries and report gaps, duplicates, units, and semantic caveats.

## Conservative Default
No-trade / benchmark-only monitoring remains the default. External data audit can improve data availability understanding, but it does not create strategy readiness. Any later strategy validation must still clear no-trade, passive BTC, expectancy, breadth, concentration, data-quality, and complexity gates.
