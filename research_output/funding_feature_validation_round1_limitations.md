# Funding Feature Validation Round 1 Limitations

- Validation was limited to the already fetched later-data OHLCV window and existing audited funding data; no new data was fetched.
- Historical Candidate D confirmation could not be fully funding-gated because audited funding starts in 2026 and the 180-observation warmup leaves only a short overlap with local OHLCV.
- Funding is 8h cadence aligned sparsely to 4h candles; no arbitrary forward-fill was used.
- Neutral-positive funding was blocked because the frozen plan required neutral-to-negative eligibility, even though positive-extreme counts are reported separately.
- OI remained diagnostic-only and did not affect eligibility.
- Base Candidate D remains parked for implementation; it was used only as a frozen research stream to test the funding gate.
- This validation does not authorize dry-run, live trading, production implementation, or parameter changes.
