=== CHATGPT HANDOFF START ===
1. run status: aggregate_taker_flow_candidate_definition_plan_round1 created as frozen-definition plan only; no validation, backtest, data fetch, tuning, source change, dry-run, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before this plan was 5746b79 research: add taker-flow data availability audit.
3. commands run: verified branch/HEAD and taker-flow audit inputs; inspected usability, computability, key-market coverage, and no-trade status; created ten aggregate taker-flow candidate definition outputs; verified files; staged only aggregate_taker_flow_candidate_definition_plan_round1.* outputs; committed and pushed.
4. files changed / output paths: research_output/aggregate_taker_flow_candidate_definition_plan_round1_note.md; _candidate_freeze.csv; _base_stream_freeze.csv; _feature_formula.csv; _alignment_rules.csv; _data_scope.csv; _metrics.csv; _pass_fail_bands.csv; _allowed_forbidden.csv; _handoff.md.
5. selected aggregate taker-flow candidate: aggregate_taker_flow_exhaustion_reversal_round1, a constrained aggregate ccy/contracts taker-flow context gate.
6. why aggregate taker-flow is constrained: audited data is 1h OKX Rubik CONTRACTS ccy aggregate taker buy/sell-like flow for 19/19 markets; exact instrument-level flow was not proven.
7. frozen base stream: 4h long-only oversold-reversal stream with RSI14 <= 30, close < EMA20, close > previous close, stop at 10-candle low - 0.5 ATR14, exits at EMA20 touch, 1.5R take profit, or 8 completed 4h candles; no add-ons or averaging down.
8. frozen taker-flow feature formula: roll complete closed 1h aggregate taker data into 4h buy/sell volumes; total = buy + sell; sell_imbalance = (sell - buy) / total; allow long only when sell_imbalance_4h >= 0.20 and data is complete/valid.
9. alignment and data scope: same 19 markets, BTC/DOGE/DOT/UNI visible, BTCUSDT_1h excluded, no market removal, no forward-fill, no future 1h bars, no partial 4h buckets, aggregate-context labeling required.
10. comparison design: compare ungated base stream, taker-flow-gated stream, no-trade, passive BTC, Candidate D later-data failure reference, and prior autonomous loop failures.
11. metrics and pass/fail bands: net PnL, PF, DD, win rate, trades, blocked entries, taker coverage, bucket performance, missed winners/avoided losers, BTC/key markets, family/concentration, no-trade/passive BTC/base comparisons; pass requires positive aggregate, PF >= 1.10 minimum, no-trade beaten, base improved, BTC non-negative when meaningful, sufficient breadth/coverage, and not just lower trade count.
12. what remains forbidden: validation now, new fetch, backtest, threshold tuning, base-rule changes, market removal, exact-instrument claims, Candidate D/K revival, dry-run/live planning, and implementation claims.
13. implementation readiness judgment: closed / not ready.
14. commit / push result: pending at file creation time; verify final response for actual commit and push result.
15. next recommended Codex prompt: Create a research-only validation plan for aggregate_taker_flow_exhaustion_reversal_round1 using the frozen definition; do not run validation yet.
16. one-sentence conclusion: The aggregate taker-flow candidate is now frozen for future research validation, but it remains constrained context and not implementation-ready.
=== CHATGPT HANDOFF END ===
