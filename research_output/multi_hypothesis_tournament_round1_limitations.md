# Multi-Hypothesis Tournament Round 1 Limitations

- The plan was executable only for non-trading baselines and passive benchmark context.
- BTC-only, regime-filtered, volatility-regime, market-family, and optional short/hedged candidates did not have exact frozen executable rules.
- No active candidate was backtested.
- Passive BTC buy-and-hold is a benchmark, not an active strategy pass.
- No new OHLCV was fetched.
- DOGE, DOT, and UNI remained included and visible in data coverage, but no active candidate generated market-specific results.
- Concentration metrics are not meaningful for no-trade and are inherently single-asset for passive BTC.
- This result cannot be used for implementation, dry-run, live trading, or PR promotion.
