# Anti-Chase Selection After Cooldown Failure Round 1

## Scope

This is a research-only single-hypothesis selection note. It does not run a backtest, validation, OHLCV fetch, source edit, parameter change, optimization, threshold sweep, PR change, dry-run restart, or live-trading plan.

## Current Closed Context

Long1-only failed its predeclared holdout gate and is parked. D2 and D6 dry-run references were negative. The frozen 6-candle cooldown hypothesis also failed: holdout net PnL -91.46, PF 0.9725, BTCUSDT -73.14 with PF 0.7461. Cooldown reduced trades from 360 -> 285 and reduced commission by 52.03, but net PnL worsened by -21.57 versus the already failed Long1 holdout.

The no-trade / capital-preservation baseline remains the default. Any next hypothesis must justify active trading after fees and drawdown rather than merely increasing activity or reducing the number of trades.

## Selected Research Hypothesis

The selected next research hypothesis for planning is an anti-chase EMA/ATR distance filter.

Purpose: avoid entering long after price has already stretched too far from EMA20 or EMA60 relative to ATR, with the goal of reducing late long entries, post-entry reversal risk, stop-loss losses after overextended entries, and EMA20 exit losses after stretched entries.

This is selected for a future predeclared validation plan only. It is not implementation-ready and it is not authorized for testing in this note.

## Why This Is Reasonable After Cooldown Failure

Cooldown tried to suppress repeated re-entry after bad exits. It reduced trades and fees, but did not improve expectancy. That suggests the next question should shift earlier in the lifecycle: whether some entries are already too stretched at the moment of entry. Anti-chase directly targets entry quality rather than post-exit waiting time.

Compared with reviving Long1-only, D2/D6, or cooldown, anti-chase is a fresh hypothesis tied to the observed failure modes:

- Late entries after price extension
- Post-entry whipsaw after stretched long signals
- Stop-loss after overextended entry
- EMA20 exit losses after chasing a move
- Fee-adjusted negative edge despite high win rate

## Comparison Against Baselines

No-trade remains the default. Anti-chase only deserves validation if a future plan freezes the rule before testing and requires positive fee-adjusted holdout PnL, PF above the predeclared gate, BTCUSDT boundary checks, market-breadth checks, and concentration controls.

Failed Long1-only is not reopened. Anti-chase may only be tested as a new entry-filter hypothesis against the failed Long1 holdout reference, not as a way to reinterpret the old candidate.

D2 and D6 remain failed operational references. Anti-chase may address post-entry whipsaw, but it must still beat no-trade and the failed references in a predeclared validation.

Cooldown is parked. Its failure shows that fewer trades and lower commission are insufficient unless expectancy improves.

## Main Risks

Anti-chase carries high threshold-overfitting risk. A distance threshold can easily become a post-result filter that removes historical losers. The next plan must freeze the distance formula, reference EMA, ATR period, and max allowed distance before testing. It must also keep DOGE/DOT/UNI visible, keep BTCUSDT visible, avoid per-market tuning, and treat reduced trade count as insufficient unless risk-adjusted results improve.

## Recommendation

Create a predeclared validation plan for anti-chase EMA/ATR distance filtering. Do not run validation yet. The plan must freeze the rule, define no-trade and failed-reference comparisons, and preserve pass/caution/fail gates before any results are observed.
