# Candidate D Confirmation Validation Limitations

- This is a research-only standalone confirmation, not implementation.
- Fixed 1,000 USDT notional and 0.05% entry/exit commission follow the batch research convention, not production sizing.
- OHLC ambiguity is handled conservatively by checking stop-loss before take-profit and EMA20 touch.
- Intrabar ambiguous holdout exits documented: 24.
- No new OHLCV was fetched; validation uses existing local 4h data only.
- BTCUSDT_1h.csv was excluded.
- Candidate D still requires synthesis and any future step must remain explicitly approved and predeclared.
- Implementation readiness remains closed / not ready.
