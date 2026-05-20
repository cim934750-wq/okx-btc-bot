# Regime-Filtered Long-Only Validation Round 1 Limitations

- This was a research-only validation of one frozen regime rule; no thresholds were swept.
- The regime filter was implemented in an inline research-only runner, not production source.
- Split-local BTCUSDT regime computation was used to stay consistent with prior chronological 70/30 validation style; warmup/missing regime states were risk_off.
- Max drawdown is reported as the max of per-market backtest drawdowns for aggregate rows, consistent with prior basket-style summaries rather than a capital-allocated portfolio equity curve.
- Blocked entries are actual blocked entries from the research runner; raw blocked starter signals are also reported separately.
- Passive BTC buy-and-hold is an opportunity-cost benchmark only, not active strategy validation.
- DOGE, DOT, and UNI remained included and visible.
- No dry-run/live/implementation readiness is implied regardless of result.
