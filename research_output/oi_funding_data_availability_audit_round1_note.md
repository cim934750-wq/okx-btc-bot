# OI/Funding Data Availability Audit Round 1

## Scope
This is a research-only data availability audit. Public historical open-interest and funding-rate data were fetched only for the same 19 approved markets mapped to OKX USDT swap candidate instruments. No backtests, strategy validation, strategy definition, parameter tuning, threshold sweep, production source change, dry-run restart, live planning, or implementation-readiness claim was made.

## Data Sources
Primary source was OKX public data through ccxt 4.2.14. Funding used `ccxt.fetchFundingRateHistory`. Historical OI used `ccxt.fetchOpenInterestHistory` with `1h` timeframe because OKX/ccxt rejected `4h` for OI history. Current exact instrument OI used `ccxt.fetchOpenInterest` for unit/provenance checks.

## Markets And Instruments
All 19 local 4h markets were audited: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. Candidate instrument IDs used the planned OKX swap mapping such as `BTCUSDT -> BTC-USDT-SWAP`. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible.

## Funding Summary
Funding rows were fetched for 19/19 markets with key-market availability = True. Funding cadence is 8h, so it maps only to every second 4h candle. Intermediate 4h funding values must remain missing unless a future fill policy is separately approved. Funding coverage range observed across markets: 2026-02-19T16:00:00+00:00 to 2026-05-23T08:00:00+00:00.

## Open Interest Summary
Historical OI rows were fetched for 19/19 markets, but the OI history method returns 1h history that appears base-currency aggregate rather than exact instrument-specific historical OI. Current exact instrument OI is available separately through the current OI endpoint. OI coverage range observed across markets: 2026-05-17T05:00:00+00:00 to 2026-05-23T08:00:00+00:00.

## Alignment Assessment
Funding is alignable to 4h only as sparse 8h events with no silent forward-fill. OI history can be downsampled/aligned from 1h to 4h, but the historical OI unit/provenance limitation must be carried into any future plan. No future strategy should treat these OI rows as exact per-instrument historical OI without a deeper native REST/vendor audit.

## Usability Decision
Overall classification: `partially_usable_needs_constraints`. Reason: Funding history is broadly usable with 8h-to-4h sparse alignment; OI history is broadly available but constrained because historical OI is 1h/base-currency aggregate while exact instrument OI is current-only in this audit.

## Recommendation
A future frozen-definition plan is possible only under constraints. The conservative next step is a funding-first or constrained funding/OI feature-definition plan, or a deeper native REST/vendor audit for exact instrument historical OI. Do not define or validate a strategy until the user explicitly approves that next step.
