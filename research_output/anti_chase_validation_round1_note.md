# Anti-Chase Validation Round 1

## Scope

This research-only validation executed the frozen anti-chase EMA/ATR entry filter from `anti_chase_validation_plan_round1`. No production source files, strategy parameters, deployment/systemd/live-loop behavior, PR #1/#2/#3, or market universe were changed. No new OHLCV was fetched and BTCUSDT_1h.csv was excluded.

## Frozen Rule

`distance_atr = (close - ema20) / atr14`

Block a new long entry when `distance_atr > 2.0`. The filter applied only to new long entries. Exits, stops, sizing, EMA/ATR periods, and market universe were preserved.

## Data Used

The validation used the same 19 local 4h markets and chronological 70/30 split used by prior holdout validation. BTCUSDT, DOGE, DOT, and UNI remained included and visible.

## Holdout Result

Anti-chase holdout aggregate:

- Trades: 346
- Net PnL: -225.26
- PF: 0.9445
- Max DD: 0.0517%
- Win rate: 64.16%
- Positive markets: 8/19

BTCUSDT holdout:

- Trades: 42
- Net PnL: -82.62
- PF: 0.7259

## Filter Effect

Holdout trades changed from 360 to 346. Actual skipped entries: 9. Raw blocked starter signals: 12. Commission changed by 9.11. Net PnL changed by -155.37 versus failed Long1 holdout.

## Exit / Mechanism Limits

Stop-loss frequency is reported only as a stop-price proxy from the backtesting trade table. Explicit EMA20-exit reason is not available from the current trade output, so EMA20-exit frequency is marked unavailable. Post-entry adverse movement is reported where inferable from OHLC bars.

## Decision

Fail: park anti-chase; no implementation.

No implementation readiness, dry-run readiness, live-trading readiness, or profitability claim is made.
