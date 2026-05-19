=== CHATGPT HANDOFF START ===
1. run status
Created no-trade / capital preservation baseline comparison plan after Long1-only holdout failure.
2. branch / workspace state
Branch: research/long1-only-candidate-robustness; workspace: /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot.
3. files changed / output paths
research_output/no_trade_capital_preservation_baseline_plan_round1_note.md; research_output/no_trade_capital_preservation_baseline_plan_round1_baselines.csv; research_output/no_trade_capital_preservation_baseline_plan_round1_candidate_gate.csv; research_output/no_trade_capital_preservation_baseline_plan_round1_allowed_forbidden.csv; research_output/no_trade_capital_preservation_baseline_plan_round1_recommended_sequence.csv; research_output/no_trade_capital_preservation_baseline_plan_round1_handoff.md.
4. why no-trade baseline is needed
Long1-only holdout failed, D2/D6 dry-run references were negative, and infrastructure success does not prove strategy edge.
5. baseline definitions
No-trade means no position, no fees, no strategy drawdown, and preserved capital except opportunity cost; future comparisons also include buy-and-hold BTC, failed Long1-only, and D2/D6 references.
6. future candidate gate
A future candidate must beat no-trade after fees, show positive holdout PnL, PF >= 1.10 by default, controlled DD, BTCUSDT non-negative if BTC-relevant, sufficient breadth, and no excessive concentration.
7. when no-trade remains preferred
No-trade remains preferred if aggregate holdout is negative, PF < 1.00, fees consume edge, DD is uncompensated, BTC fails for BTC-relevant strategy, or results rely on outliers.
8. dry-run readiness interpretation
Dry-run can only be discussed after a predeclared validation pass and explicit approval; infrastructure success alone is insufficient.
9. implementation readiness
Closed / not ready.
10. next recommended Codex prompt
Create a single-hypothesis selection note for the next research path using the no-trade baseline gate.
11. one-sentence conclusion
Future strategy work must first prove that trading is better than preserving capital.
=== CHATGPT HANDOFF END ===
