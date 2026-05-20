=== CHATGPT HANDOFF START ===
1. run status: regime_filtered_long_only_definition_plan_round1 completed as research-only frozen-definition plan; no backtests, validation, OHLCV fetch, source/parameter changes, PR changes, dry-run restart, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot.
3. commands run: verified branch/HEAD/status; inspected tournament plan/results, no-trade gate, Long1 holdout, cooldown, anti-chase, and full failure-chain outputs; created/verified definition plan files; staged/committed/pushed only regime-filtered definition files.
4. files changed / output paths: research_output/regime_filtered_long_only_definition_plan_round1_note.md; _candidate_freeze.csv; _regime_formula.csv; _data_alignment.csv; _metrics.csv; _pass_fail_bands.csv; _allowed_forbidden.csv; _handoff.md.
5. why regime-filtered candidate is selected for definition: tournament marked it not executable because classifier/lookback/allowed state were missing, and prior failures suggest weak/choppy/downtrend regimes may have damaged long-only transfer.
6. frozen regime formula: BTCUSDT 4h risk_on only when close > EMA200, EMA200 slope over 24 candles > 0, and close is not more than 20% below the 180-candle rolling high; missing/warmup state is risk_off.
7. data alignment rules: use UTC closed candles; align each market candle to same or most recent prior BTCUSDT 4h regime candle; never use future BTC data; BTCUSDT itself uses the same filter; missing anchor data blocks entries; filter blocks entries only and does not force exits.
8. metrics and pass/fail bands: net PnL, PF, max DD, win rate, trade count, blocked entries by reason, active-regime exposure, BTCUSDT, DOGE/DOT/UNI, no-trade, buy-and-hold, failed references, concentration; pass requires positive holdout, PF >= 1.10, BTCUSDT non-negative/PF >= 1.05, acceptable breadth, controlled concentration, and expectancy improvement beyond trade reduction.
9. what remains forbidden: validation now, backtests, OHLCV fetch, threshold sweeps, post-result threshold changes, weak-market removal, BTC-only rescue switch, PR/source/parameter changes, dry-run/live planning, implementation claims.
10. implementation readiness judgment: closed / not ready.
11. commit / push result: pending until commit/push completes.
12. next recommended Codex prompt: Execute regime_filtered_long_only_validation_round1 exactly according to this frozen definition plan, or pause/no-trade if not explicitly approved.
13. one-sentence conclusion: The regime-filtered candidate is now executable for a future validation without inventing rules, but it is not validated or implementation-ready.
=== CHATGPT HANDOFF END ===
