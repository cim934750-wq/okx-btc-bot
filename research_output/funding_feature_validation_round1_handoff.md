=== CHATGPT HANDOFF START ===
1. run status: funding_feature_validation_round1 executed as research-only validation; no data fetch, backtest sweep, production source/parameter change, dry-run restart, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness; based on funding_feature_validation_plan_round1.
3. commands run: loaded frozen plan, Candidate D/funding audit inputs, local 4h OHLCV, fetched later OHLCV, and audited funding; reproduced base Candidate D later-data result; applied frozen funding gate; wrote/verified outputs.
4. files changed / output paths: research_output/funding_feature_validation_round1_* plus research/funding_feature_validation_round1.py.
5. validation data used: same 19 markets, local 4h warmup, candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv, audited funding_history.csv; BTCUSDT_1h excluded.
6. frozen base stream: Candidate D research baseline only: RSI14 <= 28, close <= EMA20 - 1.5*ATR14, close > previous close, 10-candle-low minus 0.5*ATR stop, EMA20/1.5R/8-bar exits.
7. frozen funding gate: market-specific same/prior 8h funding, max 4h staleness, 180 prior observations, block positive_extreme/neutral_positive/missing/stale/warmup, allow neutral-to-negative only; OI diagnostic-only.
8. key filtered results: 7 trades, net PnL -126.242029, PF 0.000000, win rate 0.000000%, max DD 0.126242%.
9. base Candidate D comparison: base reproduced -174.234660 net PnL, PF 0.131326, 15 trades; filtered improved by 47.992631 but remained negative.
10. blocked-entry result: 10 blocked entries; blocked base-matched PnL sum -58.678553; avoided losers 7, missed winners 2.
11. funding bucket result: allowed trades came from neutral-to-negative buckets; positive-extreme and neutral-positive blocks reduced losses but did not create positive expectancy.
12. BTCUSDT result: filtered BTCUSDT net PnL -11.621598, PF 0.000000, trades 1.
13. DOGE/DOT/UNI result: DOGE 0; DOT -9.888036; UNI 0.
14. family-level result: majors -22.307520; large_alts -24.807195; defi 0; meme_high_beta 0; other -79.127315.
15. no-trade comparison: no-trade remains preferred by 126.242029 because filtered candidate net PnL is negative.
16. pass/caution/fail decision: fail.
17. what changed / did not change: changed only research outputs and research-only validation script; did not change production source, parameters, data fetch scope, thresholds, base rules, deployment, dry-run, or live state.
18. implementation readiness judgment: closed / not ready.
19. commit / push result: pending at script runtime.
20. next recommended Codex prompt: Create a research-only funding feature validation failure postmortem; keep no-trade as default and do not tune funding thresholds.
21. one-sentence conclusion: Funding avoidance reduced Candidate D later-data losses but still failed the no-trade/PF gates, so it is not implementation-ready.
=== CHATGPT HANDOFF END ===
