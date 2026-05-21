# Fresh Multi-Hypothesis Batch Round 1

## Scope

This is a research-only batch validation after final closure of the failed long-only chain. It does not restart dry-run, enable live trading, modify deployment/systemd/live-loop behavior, modify PR #1/#2/#3, change production source code, change production parameters, optimize, sweep thresholds, tune after results, remove DOGE/DOT/UNI, fetch OHLCV, or claim implementation readiness.

## Data Scope

The batch used the same 19 local 4h markets: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. `BTCUSDT_1h.csv` was excluded. The chronological 70/30 split was applied per market. BTCUSDT, DOGE, DOT, and UNI remained visible. No new/fake/inferred OHLCV was used.

## Sizing and Fees

The research-only simulator used the local `BacktestConfig` convention: initial cash 100,000 USDT per market, starter size 0.01, fixed 1,000 USDT notional per trade, and 0.05% commission on entry and exit. This is a research comparison convention only, not production sizing.

## Candidate Eligibility

All requested candidates were executable from the frozen definitions. Candidate G was treated as high-risk research only because the repository contains short-capable research backtest logic and the BTC-only short rule was fully specified. Candidate A, B, and H are non-trading baselines/benchmarks.

## Holdout Active Candidate Summary

- C_volatility_compression_breakout: net PnL 57.88, PF 1.0075754321414845, trades 534, positive markets 11/19.
- D_mean_reversion_oversold_bounce: net PnL 3853.32, PF 1.760127441945461, trades 339, positive markets 18/19.
- E_btc_relative_strength_alt: net PnL -822.20, PF 0.9635633444708986, trades 1097, positive markets 8/19.
- F_market_family_framework: net PnL -59.92, PF 0.9849235031871626, trades 276, positive markets 5/19.
- G_defensive_short_hedge: net PnL -127.26, PF 0.8715625179777207, trades 67, positive markets 0/19.

## Selection Decision

Overall decision: `one_or_more_candidates_require_separate_confirmation_before_any_dry_run_discussion`. Any top-ranked active candidate remains research-only and would require a separate confirmation validation before any dry-run discussion. Passive BTC buy-and-hold is an opportunity-cost benchmark only, not active strategy approval. Implementation readiness remains closed / not ready.
