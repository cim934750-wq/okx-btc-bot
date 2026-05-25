=== CHATGPT HANDOFF START ===
1. run status: created passive BTC versus active strategy hurdle memo outputs; no validation/backtest/data fetch was run.
2. branch / workspace state: research/long1-only-candidate-robustness at starting HEAD 8578ce2 before commit attempt.
3. commands run: inspected latest benchmark update, OHLCV tournament postmortem, candidate status, passive BTC gap, and no-trade baseline; created memo markdown/CSV files; prepared scoped verification/staging.
4. files changed / output paths: research_output/passive_btc_active_strategy_hurdle_memo_round1_note.md plus baselines.csv, hurdle_rules.csv, decision_labels.csv, c_donchian_case_study.csv, complexity_penalty.csv, anti_cherrypick_rules.csv, future_prompt_requirements.csv, allowed_forbidden.csv, handoff.md.
5. memo purpose: formalize when active strategies are worth continuing, confirming, or rejecting versus no-trade and passive BTC opportunity cost.
6. baseline definitions: no-trade is the capital-preservation floor; passive BTC is the opportunity-cost benchmark; active-strategy hurdle combines expectancy, breadth, concentration, data quality, risk, and complexity.
7. passive BTC hurdle rules: every validation must report passive BTC and active-minus-passive gap; passive BTC dominance blocks promotion unless a lower-risk or diversifying role was predeclared and proven.
8. C Donchian case study: C was positive at +3239.13 with PF 1.1643, but passive BTC was +64785.45, gap -61546.32, breadth 9 positive / 10 negative, top-3 contribution 67.07%, so it was not promoted.
9. complexity penalty: external data, ML, basis/OI/taker features, public-trade reconstruction, grid-like methods, and portfolio ranking require stronger evidence than simple OHLCV rules.
10. anti-cherry-picking rules: no market removal, threshold sweeps, best-positive promotion after failed gates, best-loser implementation path, or failed-candidate revival by renaming.
11. future prompt requirements: include no-trade, passive BTC gap, breadth, concentration, decision labels, complexity checks, and separate confirmation/readiness boundaries.
12. what remains allowed: no-trade, benchmark-only monitoring, future use of this memo as a gate, explicitly approved confirmation plans, public-trade feasibility plans, and external exact-data audit plans.
13. what remains forbidden: validation from this memo alone, strategy promotion from positive underperformers, threshold sweeps, variant spam, dry-run/live restart, and implementation-readiness claims.
14. implementation readiness judgment: none; memo only, not dry-run-ready or live-ready.
15. commit / push result: pending at file creation time.
16. next recommended Codex prompt: “Commit and push the passive BTC active-strategy hurdle memo, using plumbing fallback only if normal git commit stalls and is explicitly approved.”
17. one-sentence conclusion: Future active strategies must beat no-trade and justify themselves against passive BTC before any confirmation or readiness discussion.
=== CHATGPT HANDOFF END ===
