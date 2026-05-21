# Fresh Multi-Hypothesis Batch Round 1 Limitations

- This was a research-only batch screen, not optimization and not implementation.
- The simulator used fixed notional sizing derived from `BacktestConfig` rather than production execution logic.
- OHLC ambiguity was handled conservatively by checking stop before take-profit when both could occur in a bar.
- Chronological holdout used existing local data only; no new OHLCV was fetched.
- Candidate G is high-risk research only and does not authorize short trading.
- Candidate B passive BTC buy-and-hold is an opportunity-cost benchmark only.
- Any promising result requires separate confirmation validation before dry-run discussion.
- Implementation readiness remains closed / not ready.
