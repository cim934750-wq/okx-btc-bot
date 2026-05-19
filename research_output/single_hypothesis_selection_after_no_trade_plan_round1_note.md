# single_hypothesis_selection_after_no_trade_plan_round1

## Scope
This is a research-only single-hypothesis selection note after the Long1-only holdout failure and the no-trade / capital preservation baseline plan. It does not run a backtest, validation, OHLCV fetch, optimization, threshold sweep, source edit, PR edit, service restart, dry-run plan, or live-trading plan.

## Current State
Long1-only is parked after failing the predeclared holdout validation: holdout net PnL -69.89, PF 0.9832, BTCUSDT holdout net PnL -50.21, BTCUSDT holdout PF 0.8475, and positive markets 8/19. D2 and D6 dry-run references were negative: D2 roughly -51.92 USDT over about 7 days, and D6 early stop -103.78 USDT. Infrastructure/server operation was successful, but strategy readiness remains closed.

## Selection Objective
Choose exactly one next research hypothesis to plan, not to execute. The selected hypothesis must be compared later against the no-trade baseline, buy-and-hold BTC where relevant, the failed Long1-only holdout baseline, and D2/D6 operational failure references.

## Selected Hypothesis
Selected for future planning only: **Cooldown after exit / stop-loss**.

## Why This Hypothesis Was Selected
Cooldown after exit / stop-loss most directly targets the observed failure family without immediately choosing markets or tuning signal thresholds. It is aligned with D2/D6 post-entry whipsaw concerns, stop-loss / EMA20-exit loss concerns, and the need to test whether avoiding clustered re-entry after adverse exits can preserve capital better than continuing to trade every raw signal.

It also has clearer validation structure than broader filters: define one predeclared cooldown rule, apply it unchanged to the same validation universe, compare against no-trade and the failed Long1-only baseline, and reject it if it does not beat no-trade after fees, BTC boundary, breadth, and concentration gates.

## Why Other Hypotheses Are Not Selected Now
BTC-only is important but risky to select immediately because BTCUSDT failed the holdout. It should not be used to rescue the failed basket without a separate BTC-only framing. Regime and volatility filters may address transfer failure, but they carry high threshold-definition risk unless designed carefully. Anti-chase filters are plausible but also invite EMA/ATR distance sweeps. Market-family split and weak-market exclusion can become market selection if pursued too early. No-trade is already the baseline gate rather than the next active hypothesis.

## Next Plan Requirements
The next task should create a predeclared validation plan for cooldown only. It must define the frozen cooldown hypothesis, data scope, metrics, pass/caution/fail bands, no-trade comparison, buy-and-hold BTC comparison if BTC-relevant, failed Long1-only comparison, D2/D6 operational-reference comparison, and forbidden work. It must predefine cooldown rules before testing and explicitly forbid cooldown-length sweeps, per-market tuning, and post-result market selection.

## Implementation Readiness Boundary
Implementation readiness remains closed / not ready. This note selects a research hypothesis for future planning only. It does not authorize implementation, dry-run, live trading, source changes, or profitability claims.
