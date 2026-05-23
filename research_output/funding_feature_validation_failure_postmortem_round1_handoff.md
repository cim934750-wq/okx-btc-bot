=== CHATGPT HANDOFF START ===
1. run status: funding_feature_validation_failure_postmortem_round1 created as postmortem/synthesis only; no validation, backtest, data fetch, threshold tuning, source change, parameter change, dry-run restart, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before this postmortem was b301e3e research: add funding feature validation results.
3. commands run: verified branch/HEAD and input artifacts; created six postmortem outputs; verified output existence; staged only funding_feature_validation_failure_postmortem_round1.* files; committed and pushed after file creation.
4. files changed / output paths: research_output/funding_feature_validation_failure_postmortem_round1_note.md; _failure_reasons.csv; _loss_reduction_vs_edge.csv; _closed_items.csv; _allowed_next_steps.csv; _handoff.md.
5. funding validation failure summary: base Candidate D later-data was -174.23 PF 0.1313; funding-gated Candidate D improved to -126.24 but PF was 0.0000 and win rate was 0.00%, so the gate failed.
6. loss reduction vs edge interpretation: +47.99 improvement versus base is loss reduction only; the filtered trade set remained negative and did not create positive expectancy.
7. blocked-entry analysis: 10 entries were blocked, avoiding 7 losers totaling -85.02 and missing 2 winners totaling +26.34; blocked base net was -58.68, helpful but insufficient.
8. BTCUSDT / key-market interpretation: BTCUSDT remained negative at -11.62 PF 0.0; DOT was -9.89, DOGE and UNI had no filtered trades.
9. funding bucket interpretation: gated trades occurred only in p00-p10 and p10-p50 funding buckets and both remained negative; bucket evidence does not support implementation.
10. what is now closed: Candidate D implementation path, funding_extreme_avoidance_filter_round1 as frozen, direct funding-gated Candidate D path, dry-run/live planning, implementation readiness, and post-result tuning of this gate.
11. what remains allowed: no-trade default, benchmark-only monitoring, future OI/funding research only with a fresh frozen definition and explicit approval, deeper exact-instrument OI audit, or genuinely new feature-class inventory.
12. recommended next direction: conservative default is pause/no-trade; optional research is exact OI audit or fresh funding/OI feature inventory, not threshold tuning.
13. implementation readiness judgment: closed / not ready.
14. commit / push result: pending at file creation time; verify final response for actual commit and push result.
15. next recommended Codex prompt: Create a benchmark-only monitoring update after funding feature failure, or create a deeper exact-instrument OI audit plan; do not tune the failed funding gate.
16. one-sentence conclusion: The funding filter reduced damage but failed to turn Candidate D into a positive, tradable research edge.
=== CHATGPT HANDOFF END ===
