# Anti-Chase Validation Round 1 Limitations

- This was a research-only validation run using an inline research strategy subclass; production source files were not changed.
- The validation used only local 4h OHLCV files already present in `data/`; no new OHLCV was fetched.
- BTCUSDT_1h.csv was excluded.
- The threshold was not swept; only the predeclared `distance_atr > 2.0` rule was used.
- Explicit exit reason labels are not emitted by the backtesting trade table. Stop-loss frequency is a proxy using exit price near stop price. EMA20-exit frequency is unavailable.
- Distance-bucket output describes skipped entries and raw blocked starter signals; it is not a threshold-selection study.
- No dry-run, live trading, implementation readiness, or profitability claim is supported by this validation.
