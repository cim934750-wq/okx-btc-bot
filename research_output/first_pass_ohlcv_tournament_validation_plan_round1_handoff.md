=== CHATGPT HANDOFF START ===
1. run status: first_pass_ohlcv_tournament_validation_plan_round1 created as research-only validation plan; no validation/backtest/fetch/tuning performed.
2. branch / workspace state: research/long1-only-candidate-robustness; based on source inventory commit 06dd48c.
3. commands run: inspected source inventory and tournament plan inputs; created candidates, frozen-rule check, data scope, comparison design, metrics, ranking, pass/fail, overfit, allowed/forbidden, note, and handoff outputs.
4. files changed / output paths: research_output/first_pass_ohlcv_tournament_validation_plan_round1_* files.
5. candidates included: A_ts_momentum_ema_return_round1, B_cross_sectional_top3_round1, C_donchian_breakout_round1, D_vol_contraction_breakout_round1, E_rsi_bollinger_reversion_round1, I_regime_filtered_trend_round1.
6. frozen-rule check result: all six use source-inventory rules; minor operational ambiguities for B ranking/trailing mechanics, D percentile timing, and I realized-volatility window are explicitly marked for approval before execution.
7. data scope: existing local 4h OHLCV only, same 19 markets where feasible, BTCUSDT/DOGEUSDT/DOTUSDT/UNIUSDT visible, BTCUSDT_1h/funding/OI/taker/basis/private data excluded.
8. comparison design: each candidate must compare against no-trade, passive BTC, buy-and-hold where feasible, other tournament candidates, and failed references as context only.
9. metrics and ranking method: PnL, PF, DD, win rate, avg/median trade, trade count, exposure, fees, BTC/key-market results, breadth, concentration, baselines, data coverage; ranking prioritizes decision, PnL, PF, DD, breadth, BTC, concentration, sample size, BTC benchmark, simplicity.
10. pass/fail gates: pass requires positive net PnL after fees, PF >= 1.10 minimum, no-trade beaten, BTC benchmark reported, BTCUSDT non-negative if meaningful, breadth, clean data, no leakage, and no implementation claim.
11. overfitting controls: one frozen candidate per family, no sweeps, same 19 markets, same costs/sizing, closed candles only, chronological split, failed references context only.
12. what remains forbidden: validation, backtests, data fetch, tuning, multiple variants, market removal, source/parameter/PR/deployment changes, dry-run/live planning, implementation-readiness claims.
13. implementation readiness judgment: none; this is a validation plan only.
14. commit / push result: pending at file creation time; verify final response for actual commit and push result.
15. next recommended Codex prompt: Execute first_pass_ohlcv_tournament_validation_round1 exactly according to the plan; do not change frozen rules, data scope, or thresholds.
16. one-sentence conclusion: The six-candidate OHLCV tournament is now predeclared and ready for an explicitly approved execution task, but no validation has been run.
=== CHATGPT HANDOFF END ===
