=== CHATGPT HANDOFF START ===
1. run status: regime_filtered_long_only_validation_round1 completed as research-only validation; no production source/parameter/PR/deployment/dry-run/live changes.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot.
3. commands run: verified branch/HEAD/status; inspected frozen definition and prior references; ran inline research-only validation over 19 local 4h markets with BTCUSDT regime anchor; ran py_compile and compileall; generated/verified outputs; staged/committed/pushed only validation outputs.
4. files changed / output paths: research_output/regime_filtered_long_only_validation_round1_note.md; _aggregate_metrics.csv; _market_metrics.csv; _regime_exposure.csv; _blocked_entries.csv; _blocked_by_reason.csv; _btcusdt_assessment.csv; _weak_market_assessment.csv; _no_trade_comparison.csv; _buy_hold_comparison.csv; _failed_reference_comparison.csv; _concentration.csv; _decision.csv; _limitations.md; _handoff.md; _data_coverage.csv.
5. validation data used: same 19 local 4h markets; BTCUSDT_4h regime anchor; BTCUSDT_1h excluded; chronological 70/30 split; no new/fake/inferred OHLCV.
6. frozen regime rule: risk_on only if BTCUSDT close > EMA200, EMA200 slope over 24 candles > 0, and BTC close is not more than 20% below 180-candle rolling high; missing/warmup risk_off; entries blocked only, no force exits.
7. key aggregate results: holdout trades 322; net PnL -266.26; PF 0.9318; win rate 63.35%; positive markets 6/19.
8. regime exposure / blocked-entry result: holdout active-regime exposure 47.00%; raw blocked starter signals 37; actual blocked entries 36.
9. BTCUSDT result: trades 44; net PnL -30.08; PF 0.9021; boundary fail.
10. DOGE/DOT/UNI result: DOGEUSDT -287.14/PF 0.3586; DOTUSDT 7.81/PF 1.1487; UNIUSDT 436.62/PF 2.2267.
11. no-trade comparison: holdout candidate minus no-trade -266.26; does not beat no-trade.
12. buy-and-hold comparison: passive BTC holdout return 64.7854% and normalized PnL per 100k 64785.45; benchmark only, not active strategy validation.
13. failed-reference comparison: compared against failed Long1, D2, D6, cooldown, and anti-chase; beating any failed reference alone is insufficient.
14. pass/caution/fail decision: fail; reasons aggregate_holdout_negative_or_not_positive|profit_factor_below_1|BTCUSDT_negative|basket_breadth_below_10_positive_markets|nonpositive_avg_trade_expectancy|regime_filter_blocked_entries_but_did_not_beat_no_trade.
15. what changed / did not change: added research_output validation files only; production source, strategy parameters, PRs, data, deployment, dry-run/live behavior unchanged.
16. implementation readiness judgment: closed / not ready.
17. commit / push result: pending until commit/push completes.
18. next recommended Codex prompt: Create a failure/synthesis postmortem if failed, or confirmation-validation plan if passed; do not discuss dry-run/live.
19. one-sentence conclusion: The frozen regime filter was validated conservatively and remains research-only with no implementation claim.
=== CHATGPT HANDOFF END ===
