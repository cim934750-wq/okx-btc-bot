=== CHATGPT HANDOFF START ===
1. run status: Candidate D synthesis and confirmation-validation plan created as research-only plan; no new backtests, validation, OHLCV fetch, source changes, parameter changes, dry-run, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot.
3. commands run: verified branch/HEAD; inspected fresh batch aggregate, selection, BTC, weak-market, family, and concentration outputs; created plan/synthesis outputs; verified outputs; staged only Candidate D plan files; committed and pushed.
4. files changed / output paths: research_output/candidate_d_mean_reversion_synthesis_round1_note.md; _evidence.csv; _risks.csv; candidate_d_mean_reversion_confirmation_plan_round1_candidate_freeze.csv; _metrics.csv; _pass_fail_bands.csv; _allowed_forbidden.csv; _handoff.md.
5. Candidate D evidence summary: holdout net PnL +3853.32, PF 1.7601, 339 trades, BTCUSDT +253.84/PF 2.3689, positive markets 18/19, DOGE and DOT positive, positive across families.
6. why Candidate D differs from failed Long1 family: it is oversold mean-reversion, not trend continuation or breakout chasing; it uses shorter holds, no add-ons, and no averaging down.
7. main risks: crash-regime failure, stop width mismatch, sample/regime dependence, family/rebound concentration, lookahead/OHLC ambiguity, and implementation mismatch.
8. confirmation validation objective: verify Candidate D as a standalone frozen candidate using the same exact rules and no parameter changes.
9. frozen candidate rules: RSI14 <= 28; close <= EMA20 - 1.5 ATR14; close > previous close; stop = 10-candle low - 0.5 ATR14; exit at EMA20 touch, 1.5R, or 8 completed 4h candles; no averaging down or add-ons.
10. confirmation metrics: PnL, PF, DD, win rate, avg/median trade, trade count, hold time, exit frequencies, BTCUSDT, DOGE/DOT/UNI, family, concentration, no-trade, buy-and-hold, failed-reference, and alignment audits.
11. pass/caution/fail bands: pass requires positive holdout, PF >= 1.20 preferred with minimum >= 1.10, BTCUSDT non-negative/PF >= 1.05, no-trade beaten, controlled DD, and no excessive concentration.
12. what remains forbidden: parameter tuning, threshold sweeps, RSI/ATR/EMA/R/stop/time-stop changes, market removal, dry-run/live planning, and implementation claims.
13. implementation readiness judgment: closed / not ready.
14. commit / push result: Candidate D plan outputs committed and pushed on research/long1-only-candidate-robustness.
15. next recommended Codex prompt: Execute Candidate D confirmation validation exactly according to candidate_d_mean_reversion_confirmation_plan_round1.
16. one-sentence conclusion: Candidate D is promising enough for standalone confirmation, but it is not implementation-ready and authorizes no trading action.
=== CHATGPT HANDOFF END ===
