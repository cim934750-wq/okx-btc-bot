=== CHATGPT HANDOFF START ===
1. run status: funding_feature_candidate_definition_plan_round1 completed as research-only frozen-definition plan; no validation/backtest/fetch/tuning/source/deployment changes.
2. branch / workspace state: research/long1-only-candidate-robustness; based on 07d8c5d.
3. commands run: verified branch/HEAD; inspected OI/funding audit outputs, feature inventory, autonomous failure context, and 19-market data scope; created/verified definition-plan outputs; staged/committed/pushed only new funding plan files.
4. files changed / output paths: research_output/funding_feature_candidate_definition_plan_round1_*.
5. selected funding candidate: funding_extreme_avoidance_filter_round1.
6. why funding-first is selected over OI-first: funding is usable for 19/19 markets; historical OI is only partially usable because it is 1h/base-currency aggregate and not exact instrument-specific via the current route.
7. frozen funding formula: market-specific current funding from same/prior <=4h funding timestamp; 180 prior observations; positive extreme >=90th percentile blocks longs; neutral-to-negative eligibility requires funding <=0 or percentile <=50; negative extreme <=10 is diagnostic only.
8. funding alignment rules: 8h funding on 4h strategy grid, no future leakage, max staleness 4h, no arbitrary forward-fill, missing/stale/warmup blocks entries.
9. data scope: same 19 markets with BTCUSDT, DOGEUSDT, DOTUSDT, UNIUSDT visible; OI diagnostic-only; no market removal.
10. metrics and pass/fail bands: future validation must report PnL/PF/DD/win rate/trades, blocked entries by funding state, bucket performance, BTC/key markets, concentration, no-trade/passive BTC/failed-reference comparisons, missing/stale funding; pass needs positive aggregate, PF >=1.10 minimum, no-trade beaten, BTC non-negative if meaningful, improved expectancy, and no concentration.
11. what remains forbidden: validation/backtests in this task, data fetch, funding threshold/window sweeps, OI substitution after results, market removal, failed-candidate revival, dry-run/live, implementation claim.
12. implementation readiness judgment: closed / not ready.
13. commit / push result: pending at file creation time.
14. next recommended Codex prompt: Create a predeclared validation plan for funding_extreme_avoidance_filter_round1, including the frozen base entry/exit stream it will gate; do not run validation yet.
15. one-sentence conclusion: Funding can now be planned as a frozen crowding-avoidance feature gate, but it is not a strategy and not implementation-ready.
=== CHATGPT HANDOFF END ===
