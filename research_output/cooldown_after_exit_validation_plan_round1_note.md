# cooldown_after_exit_validation_plan_round1

## Scope
This is a research-only predeclared validation plan for the selected hypothesis: cooldown after exit / stop-loss. It does not run a backtest, validation, OHLCV fetch, optimization, threshold sweep, source edit, PR edit, service restart, dry-run plan, or live-trading plan.

## Current Context
Long1-only failed the predeclared holdout validation and is parked. Holdout net PnL was -69.89, PF was 0.9832, BTCUSDT holdout net PnL was -50.21, BTCUSDT PF was 0.8475, and positive markets were 8/19. D2 dry-run was roughly -51.92 USDT over about 7 days. D6 early-stop dry-run was -103.78 USDT. The no-trade / capital preservation baseline is now required. The current bot service is stopped, and no dry-run/live continuation is authorized.

## Hypothesis
The hypothesis is that part of the failed active-trading behavior comes from post-entry whipsaw, stop-loss / EMA20-exit losses, and repeated re-entry too soon after adverse exits. A fixed cooldown after these exits may reduce clustered re-entry losses, fees, and drawdown enough to beat the no-trade baseline in future validation.

This is not an implementation candidate. It is a hypothesis for future validation planning only.

## Frozen Primary Cooldown Rule
Primary rule for a future validation run:

- If a market records an exit with reason `confirmed_close_below_ema20`, block new entries on that same market for the next 6 completed 4h candles after the exit candle.
- If a market records an exit with reason `stop_loss`, block new entries on that same market for the next 6 completed 4h candles after the exit candle.
- If both cooldown conditions overlap, use the later cooldown expiry.
- The cooldown is per market, not global across all markets.
- The cooldown blocks new entries only; it must not modify existing position management, exit rules, indicators, thresholds, or strategy parameters.
- The primary cooldown length is fixed at 6 candles, equal to 24 hours on 4h data.

The 6-candle choice is conservative enough to avoid immediate re-entry after adverse exits but not so long that the plan intentionally collapses trade frequency. It is selected before testing and must not be changed after seeing results.

## Secondary Sensitivity Boundary
Secondary sensitivity is allowed only after the primary result is completed, documented, and explicitly approved. Sensitivity may examine whether the primary result is robust to nearby cooldown lengths, but it must not be used to select the best value for implementation. No secondary sensitivity is authorized by this plan.

## Data Scope
Future validation should use the same 19 local 4h markets, with chronological split matching the prior Long1-only holdout framework unless a later plan explicitly approves new data. BTCUSDT remains visible. DOGE, DOT, and UNI remain included and visible. BTCUSDT_1h remains excluded unless separately scoped. No post-result market removal is allowed.

## Required Comparisons
Future validation must compare the cooldown hypothesis against: no-trade baseline, buy-and-hold BTC if BTC-relevant, failed Long1-only holdout, D2/D6 negative dry-run references, and the non-cooldown Long1-only reference. The comparison must not reopen Long1-only as a base candidate.

## Pass / Caution / Fail Boundary
Pass requires fee-aware positive holdout net PnL, PF >= 1.10 by default, BTCUSDT non-negative with PF >= 1.05 if BTC-relevant, controlled max DD, evidence of reduced whipsaw/re-entry losses, no excessive concentration, and no hiding/removal of weak markets. Passing would mean continue research only, not implementation readiness.

Caution applies if aggregate improves but remains marginal, PF is 1.00 to <1.10, BTCUSDT is weak, trade count collapses, fee reduction is the only visible benefit, or concentration remains high.

Fail applies if aggregate holdout is negative, PF < 1.00, BTCUSDT is negative, cooldown only reduces trades without improving risk-adjusted results, gains come from outliers only, weak markets are hidden or removed, or results resemble the failed Long1-only/D2/D6 references.

## Forbidden Work
Forbidden: cooldown length sweep, choosing cooldown length after seeing results, per-market cooldown tuning, dropping DOGE/DOT/UNI, market cherry-picking, source edits in this plan, strategy parameter changes, optimization, threshold sweep, dry-run/live planning, implementation-readiness claim, profitability claim, and PR #1/#2/#3 modification.

## Recommendation
Next step, if explicitly approved, should be to execute exactly this primary cooldown validation plan. Until then, no validation or implementation action is authorized.
