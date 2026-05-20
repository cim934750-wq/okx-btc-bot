=== CHATGPT HANDOFF START ===
1. run status: anti_chase_validation_plan_round1 completed as plan-only; no validation/backtest/OHLCV/source/parameter changes.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot.
3. commands run: verified branch/latest commit, inspected prior anti-chase selection/no-trade/Long1/cooldown outputs, generated plan outputs, verified outputs, staged/committed/pushed only new plan files.
4. files changed / output paths: research_output/anti_chase_validation_plan_round1_note.md; _candidate_freeze.csv; _formula.csv; _metrics.csv; _pass_fail_bands.csv; _allowed_forbidden.csv; _handoff.md.
5. selected anti-chase hypothesis: research-only long-entry anti-chase EMA/ATR distance filter.
6. frozen formula and threshold: distance_atr = (close - ema20) / atr14; block long entry when distance_atr > 2.0; threshold is a conservative non-swept 2.0 ATR cap.
7. validation data scope: same 19 local 4h markets, chronological 70/30 split, BTCUSDT visible, DOGE/DOT/UNI visible, BTCUSDT_1h excluded, no new/fake/inferred OHLCV.
8. metrics: net PnL, PF, max DD, win rate, avg/median trade, trade count, skipped entries, skipped entries by market/distance bucket if feasible, fee reduction, post-entry adverse movement if feasible, stop-loss/EMA20-exit frequency if available, BTCUSDT, DOGE/DOT/UNI, breadth, concentration, no-trade and failed-reference comparisons.
9. pass/caution/fail bands: pass requires positive holdout after fees, PF >= 1.10, BTCUSDT non-negative with PF >= 1.05, controlled DD, reduced overextended-entry losses, breadth/concentration controls; fail includes aggregate negative, PF < 1.00, BTC negative, trade reduction without expectancy improvement, hidden weak markets, or cherry-picked threshold.
10. no-trade baseline interpretation: no-trade remains default unless the frozen anti-chase candidate beats it after fees and drawdown.
11. what remains forbidden: validation now, backtests now, OHLCV fetch, source/parameter changes, optimization, threshold sweep, market removal, PR changes, dry-run/live planning, implementation-readiness claim.
12. implementation readiness judgment: closed / not ready.
13. commit / push result: pending until git commit/push completes.
14. next recommended Codex prompt: Execute anti_chase_validation_round1 exactly according to anti_chase_validation_plan_round1.
15. one-sentence conclusion: The anti-chase plan freezes one entry-distance filter for future validation without promoting it to implementation.
=== CHATGPT HANDOFF END ===
