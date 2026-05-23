=== CHATGPT HANDOFF START ===
1. run status: funding_feature_validation_plan_round1 created as a research-only predeclared validation plan; no validation, backtest, data fetch, source change, parameter change, PR change, dry-run restart, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness; based on 2b9ce23 research: add funding feature candidate definition plan.
3. commands run: verified branch/HEAD; inspected funding candidate definition plan, OI/funding audit outputs, Candidate D later-data failure postmortem, and funding data-scope constraints; created and verified validation-plan outputs; staged/committed/pushed only new funding validation plan files.
4. files changed / output paths: research_output/funding_feature_validation_plan_round1_note.md; _base_stream_freeze.csv; _funding_gate_freeze.csv; _alignment_rules.csv; _data_scope.csv; _metrics.csv; _pass_fail_bands.csv; _allowed_forbidden.csv; _handoff.md.
5. validation objective: compare frozen Candidate D base stream versus the same stream gated by funding_extreme_avoidance_filter_round1 to test whether funding avoidance improves robustness without merely reducing trades.
6. frozen base stream: 4h Candidate D research baseline only: RSI14 <= 28, close <= EMA20 - 1.5*ATR14, close > previous close, stop at recent 10-candle low - 0.5*ATR14, exits at EMA20 touch, 1.5R take profit, or 8-bar time stop, no add-ons or parameter changes.
7. frozen funding gate: market-specific funding; same/prior timestamp only; max staleness 4h; 180 prior observations; block percentile >=90, neutral-positive, missing, stale, or warmup-insufficient; allow only valid neutral-to-negative funding; negative extreme diagnostic only.
8. alignment and data scope: 8h funding aligned sparsely to 4h candles with no future leakage or arbitrary forward-fill; same 19 markets with BTCUSDT/DOGE/DOT/UNI visible; OI diagnostic-only; BTCUSDT_1h excluded; no new data fetch in this plan.
9. comparison design: future validation must report base Candidate D, funding-gated Candidate D, no-trade, passive BTC, Candidate D later-data failure, and failed-reference comparisons over identical eligible windows.
10. metrics and pass/fail bands: include PnL, PF, DD, win rate, avg/median trade, trade count, blocked entries, missed winners/avoided losers, funding buckets, key markets, family results, concentration, funding coverage, warmup/stale counts, and slippage/fee sensitivity if feasible; pass needs positive after fees, PF >=1.10 minimum, no-trade beaten, base improvement, BTC safety, and no excessive concentration.
11. what remains forbidden: validation/backtests/fetching in this task, tuning, threshold/window/staleness changes, OI as primary feature, market removal, dry-run/live planning, source/parameter/deployment changes, and implementation claims.
12. implementation readiness judgment: closed / not ready.
13. commit / push result: pending at file creation time.
14. next recommended Codex prompt: Execute funding_feature_validation_round1 exactly according to funding_feature_validation_plan_round1; do not change thresholds, base stream, or data scope.
15. one-sentence conclusion: The funding feature now has a decision-complete validation plan, but it remains research-only and unvalidated.
=== CHATGPT HANDOFF END ===
