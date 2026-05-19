# research_reset_after_long1_failure_round1

## Scope
This is a research-only reset / new hypothesis inventory note after `long1_only_holdout_validation_round1` failed. It does not run a backtest, validation, OHLCV fetch, optimization, threshold sweep, source edit, PR edit, deployment change, dry-run plan, or live-trading plan.

## Current Decision State
Long1-only is parked. It failed the predeclared holdout gate: holdout net PnL -69.89, holdout PF 0.9832, BTCUSDT holdout net PnL -50.21, BTCUSDT holdout PF 0.8475, and positive markets 8/19. The current decision remains: Long1-only is not the base candidate and must not be reopened without a new, explicitly approved hypothesis and fresh predeclared gates.

## Why Long1-only Is Closed
The reference segment was strong, but the predeclared 30% chronological holdout did not confirm the candidate. The holdout aggregate was negative, PF was below 1.00, BTCUSDT failed, and market breadth was below the pass threshold. This is enough to close Long1-only as the current base path regardless of reference-period strength.

D2 and D6 dry-run evidence also does not rescue the path. D2 was roughly -51.92 USDT over roughly 7 days; D6 was -103.78 USDT early stop. These are not formal holdout replacements, but they reinforce that dry-run continuation is not authorized.

## Infrastructure Success vs Strategy Failure
Server/GCP operation can be treated as infrastructure validation only. It does not convert a failed research candidate into a tradable strategy. Infrastructure being able to run the bot is separate from whether the strategy has robust edge. The bot service is stopped, and no live or dry-run continuation is authorized.

## Evidence That Must Not Be Overused
- Reference-period strength: useful history, but invalid as a substitute for failed holdout.
- Isolated UNI strength: not enough to override failed aggregate, BTCUSDT failure, or weak breadth.
- BTC-only hopes: require a separate BTC-only hypothesis with predeclared gates; BTCUSDT failed this holdout.
- Concentration metrics: cannot be used as pass evidence when aggregate holdout PnL is negative.
- Weak-market removal: DOGE/DOT/UNI or other weak symbols cannot be removed after seeing results.

## Hypothesis Inventory Boundary
The hypotheses below are inventory items, not selected candidates. None authorizes implementation, dry-run, parameter tuning, or market cherry-picking. Any future work must choose one hypothesis in advance, freeze rules before testing, and define pass/caution/fail gates before seeing new results.

## Recommended Research Sequence
1. Create a formal hypothesis-selection note and choose exactly one next hypothesis before testing.
2. Prefer a no-trade / capital preservation baseline comparison first, because it sets the minimum bar after multiple failed or parked strategy paths.
3. If continuing directional research, define either BTC-only or regime-filtered long-only as a separate predeclared study, not as a revival of Long1-only.
4. Only after a hypothesis passes fresh gates should any outlier, weak-market, or BTC-vs-basket follow-up be considered.
5. Keep implementation readiness closed until separate validation proves robustness and the user explicitly approves a later readiness discussion.

## Closed Work
Closed: Long1-only as base candidate, Long1-only dry-run discussion, production implementation, profitability claims, current Long1-only branch as a strategy base, and any attempt to reuse reference-period strength as validation.

## Allowed Remaining Work
Allowed: postmortem-only analysis, a separately approved BTC-only research path with predeclared gates, new candidate research with fresh gates, weak-market failure review without cherry-picking, and no-trade baseline comparisons.

## Forbidden Work
Forbidden: reopening Long1-only as the base candidate, optimization, threshold sweeping, choosing markets after seeing results, removing DOGE/DOT/UNI post-result, live/dry-run planning, implementation readiness claims, production merge claims, and profitability claims from failed or in-sample evidence.

## Recommendation
Park Long1-only and reset research around a new predeclared hypothesis. Do not select a final new candidate in this note. The next safe action is a hypothesis-selection / predeclared gate note.
