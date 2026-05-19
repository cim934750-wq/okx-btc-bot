# cooldown_after_exit_validation_round1

## Scope
Executed the predeclared 6-candle cooldown-after-exit validation as a research-only validation. No production strategy source, parameters, deployment/systemd/live-loop behavior, PR #1/#2/#3, dry-run service, or live trading state was changed.

## Data
Used the same 19 local 4h markets with chronological 70% reference / 30% holdout splits. BTCUSDT_1h.csv was excluded. DOGE, DOT, and UNI remained included and visible. No new OHLCV was fetched.

## Frozen Cooldown Rule
After `confirmed_close_below_ema20` or `stop_loss` exit, same-market new entries were blocked for the next 6 completed 4h candles. Positions already open were not force-closed by cooldown. No other cooldown length was tested.

## Aggregate Result
Reference cooldown result: trades 958, net PnL 5110.56, PF 1.3173.
Holdout cooldown result: trades 285, net PnL -91.46, PF 0.9725, max DD 0.0476%, win rate 63.86%.

## Cooldown Effect
Holdout cooldown events: 310. Holdout skipped entries: 86. Trade count changed from 360 to 285. Net PnL delta versus failed Long1 holdout rerun: -21.57. Commission reduction: 52.03.

## BTCUSDT Boundary
BTCUSDT holdout cooldown result: net PnL -73.14, PF 0.7461, trades 39. BTCUSDT remains a required visible boundary for this BTC-relevant research path.

## Decision
Fail: cooldown does not beat no-trade gate; do not advance.

## Boundary
This does not prove profitability, does not revive Long1-only as a base candidate, and does not authorize dry-run, live trading, source promotion, or implementation readiness.
