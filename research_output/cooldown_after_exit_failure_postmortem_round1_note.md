# Cooldown After Exit Failure Postmortem Round 1

## Scope

This is a research-only postmortem/synthesis for `cooldown_after_exit_validation_round1`. No new backtests, validations, OHLCV fetches, source edits, parameter changes, optimization, threshold sweeps, dry-run planning, live planning, or PR changes were performed.

## Validation Result

The frozen cooldown hypothesis failed the predeclared gate on the same 19 local 4h markets using the chronological 70/30 split. No new OHLCV was fetched. The tested rule blocked same-market new entries for the next 6 completed 4h candles after either `confirmed_close_below_ema20` or `stop_loss` exits.

Holdout cooldown results:

- Trades: 285
- Net PnL: -91.46
- Profit factor: 0.9725
- Max DD: 0.0476%
- Win rate: 63.86%

The fail condition was triggered because aggregate holdout PnL was negative, profit factor was below 1.00, BTCUSDT was negative, and the cooldown worsened the failed Long1 holdout reference.

## Why Cooldown Failed

Cooldown reduced activity but did not improve edge. Holdout trades fell from 360 to 285, 86 entries were skipped, and commission fell by 52.03. Despite that, net PnL worsened from -69.89 to -91.46 and profit factor slipped from 0.9832 to 0.9725. Lower fees are not enough when the remaining trades still produce negative expectancy.

## BTCUSDT Boundary

BTCUSDT failed under the cooldown rule with 39 trades, net PnL -73.14, and PF 0.7461. Because BTCUSDT is central to this project context, this blocks advancement. BTC failure cannot be offset by isolated strength in other markets without a separate, predeclared non-BTC or market-specific research path.

## DOGE / DOT / UNI Interpretation

DOGE remained a serious weak-market result at -364.54 with PF 0.1480. DOT was slightly positive at +7.81 but only had 3 trades, so it is not strong rescue evidence. UNI stayed positive at +402.58 and PF 2.6313, but one strong market cannot override aggregate holdout failure, BTCUSDT failure, and DOGE weakness. DOGE, DOT, and UNI were retained and visible as required; none can be removed after seeing results.

## Closed Work

The following are closed from this evidence:

- Long1-only as the base candidate
- D2/D6 continuation as dry-run candidates
- Frozen 6-candle cooldown hypothesis
- Cooldown dry-run/live planning
- Production implementation path from this candidate
- Implementation-readiness claim
- Profitability claim from this validation

## Allowed Next Steps

The no-trade / capital-preservation baseline remains the default. Allowed future work is limited to research-only next hypotheses with fresh selection and predeclared plans, such as an anti-chase EMA/ATR distance filter or a BTC-only path with a separate gate. No future path should reuse this failure as implementation evidence.

## Recommendation

Park the frozen cooldown hypothesis. Do not advance it to dry-run, live planning, or implementation. If research continues, create a fresh hypothesis selection/plan before any new validation is run.
