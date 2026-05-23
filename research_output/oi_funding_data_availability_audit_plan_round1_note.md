# OI/Funding Data Availability Audit Plan Round 1

## Scope
This is a research-only data-availability audit plan. It does not fetch data, run backtests, run validation, define a trading strategy, tune parameters, sweep thresholds, change source code, change production parameters, restart dry-run, create live trading plans, or claim implementation readiness.

## Audit Objective
Before any new strategy definition, determine whether open-interest and funding-rate history are available, clean, timestamped, unit-consistent, and alignable to the same 4h OHLCV research universe. The audit must cover the same 19 markets used in prior validation: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT must remain visible.

## Why This Audit Comes Before Strategy Work
The prior OHLCV-only research path failed, Candidate D failed fetched later-data validation, and the autonomous discovery loop promoted zero candidates. The top-ranked new feature classes were `open_interest` and `funding_rate`, but their usefulness depends on actual historical coverage and correct instrument mapping. Strategy definitions before data coverage would invite invented assumptions and overfitting.

## Instruments To Check
For each spot-style local symbol, the future audit should check the OKX USDT-margined perpetual/swap instrument candidate `BASE-USDT-SWAP`. Availability is not assumed. Missing instruments must be reported as missing, not replaced.

## Alignment Principles
OI and funding observations must be aligned to the 4h OHLCV grid without future leakage. Funding rates often settle every 8h, so the future audit must distinguish settled historical rates from current/predicted rates before any feature can be used. Open interest sampling frequency must be documented, and missing values must not be forward-filled by default.

## Coverage Requirements
A future audit must report start/end timestamps per market, overlap with prior reference/holdout windows, later-data availability, missing markets, gaps, duplicate timestamps, timezone consistency, source/provenance, and unit conventions. Data can be `usable_for_research`, `partially_usable`, or `not_usable` based on the criteria in the usability file.

## Recommendation
Next step: execute a data-availability audit/fetch only after explicit approval. Do not define OI/funding strategy rules until coverage, units, and alignment quality are known. No-trade / benchmark-only observation remains the default.
