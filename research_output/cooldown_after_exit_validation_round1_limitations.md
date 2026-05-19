# cooldown_after_exit_validation_round1 limitations

- This was a research-only validation execution using local historical 4h CSVs only.
- No new OHLCV was fetched.
- BTCUSDT_1h.csv was excluded.
- DOGE, DOT, and UNI remained included and visible.
- The validation used a research-only dynamic strategy class and did not edit production source files.
- `confirmed_close_below_ema20` is applied as a research event when a long exit occurs with current close below EMA20 or when the trend-fail close path occurs below EMA20.
- `stop_loss` is applied when a long trade closes through an active stop/SL order in the backtesting engine.
- Skipped entries are counted only when a `starter_long_signal` appears while the same-market cooldown is active and baseline entry timing gates would otherwise allow entry.
- Skipped entries are not assigned invented hypothetical trade PnL.
- D2/D6 values are negative operational references, not validation replacements.
- Implementation readiness remains closed / not ready.
