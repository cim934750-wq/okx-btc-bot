# Aggregate Taker-Flow Validation Round 1 Limitations

- Taker-flow data is `aggregate_ccy_contracts_context_not_exact_instrument_flow`; it is not exact instrument-level taker flow.
- Validation used existing audited taker-flow raw data only; no new fetch was performed.
- The later-data OHLCV window is short for most non-BTC markets, so trade-count interpretation remains sample-limited.
- 1h taker rows were aggregated into closed 4h buckets; incomplete buckets were blocked, not filled.
- No arbitrary forward-fill or future 1h rows were used.
- Candidate D and autonomous loop failures are comparison references only and were not revived as implementation candidates.
- This validation does not authorize dry-run, live trading, implementation readiness, parameter tuning, threshold changes, or market removal.
