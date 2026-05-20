# Anti-Chase Failure Postmortem Round 1

## Scope

This is a research-only failure postmortem/synthesis for `anti_chase_validation_round1`. No new backtests, validations, OHLCV fetches, source edits, parameter changes, optimization, threshold sweeps, alternative anti-chase thresholds, PR changes, dry-run restarts, live-trading plans, or implementation-readiness claims were performed.

## Validation Result

The frozen anti-chase EMA/ATR distance filter failed the predeclared gate. The validation used the same 19 local 4h markets and chronological 70/30 split. `BTCUSDT_1h.csv` was excluded and no new OHLCV was fetched.

Frozen rule:

`distance_atr = (close - ema20) / atr14; block new long entry when distance_atr > 2.0`

Holdout anti-chase result:

- Trades: 346
- Net PnL: -225.26
- Profit factor: 0.9445
- Max DD: 0.0517%
- Win rate: 64.16%
- Positive markets: 8/19

The fail condition was triggered by negative aggregate holdout PnL, PF below 1.00, BTCUSDT negative, and worse results than the already failed Long1-only, cooldown, D2, and D6 references.

## Why Anti-Chase Failed

Anti-chase did not convert reduced activity into positive expectancy. It reduced trades from 360 -> 346, skipped 12 actual entries, recorded 9 raw blocked starter signals, and reduced commission by 9.11. However, holdout net PnL worsened by -155.37 versus the failed Long1-only holdout. The average trade also worsened, so the filter reduced activity without improving the quality of the remaining trades.

The blocked overextended-entry sample was too small to materially improve the system. It also removed positive historical holdout contribution rather than isolating a reliable loss pocket. This confirms that a slight reduction in trades and fees is not equivalent to edge improvement.

## BTCUSDT Boundary

BTCUSDT failed with 42 trades, net PnL -82.62, and PF 0.7259. This blocks advancement because BTCUSDT is central to this project context. BTCUSDT failure cannot be rescued by isolated positive markets without a separate BTC/non-BTC framing and predeclared validation gate.

## DOGE / DOT / UNI Interpretation

DOGE remained weak at -287.14 with PF 0.3586. DOT was positive at 7.81 with PF 1.1487, but the absolute contribution is too small to rescue the candidate. UNI was positive at 380.59 with PF 1.9826, but UNI strength does not override aggregate failure, BTCUSDT failure, and DOGE weakness. DOGE, DOT, and UNI remained visible and must not be hidden or removed after results.

## Failed Reference Comparison

Anti-chase was worse than failed Long1 by -155.37, worse than failed cooldown by -133.80, worse than D2 by -173.34, and worse than D6 by -121.48. These are negative references, not implementation paths.

## Closed Work

The following are closed from this evidence:

- Long1-only as base candidate
- D2/D6 continuation as dry-run candidates
- Frozen 6-candle cooldown hypothesis
- Frozen anti-chase EMA/ATR distance filter
- Dry-run/live planning
- Production implementation path from these candidates
- Implementation-readiness claim
- Profitability claim from this validation

## What Remains Allowed

The no-trade / capital-preservation baseline remains the default. Allowed future work is limited to postmortem-only analysis, a BTC-only path only with a separate predeclared gate, a new hypothesis only after fresh selection and planning, or weak-market/failure analysis without cherry-picking. Any new validation must start from a fresh plan and must not reuse these failed candidates as implementation evidence.

## Recommendation

Park anti-chase as currently frozen. Do not advance it to dry-run, live planning, or implementation. The conservative next direction is to pause research and keep no-trade as default. If research continues, create a new hypothesis inventory before selecting anything else.
