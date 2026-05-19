# long1_only_holdout_validation_round1

## Scope
Executed the predeclared Long1-only holdout validation plan. This is research-only validation execution, not implementation planning. No source files, parameters, thresholds, PR branches, deployment behavior, live-loop behavior, or market universe were changed.

## Candidate
Frozen Long1-only: allow_longs=True, allow_shorts=False, enable_add_on_entries=False. Long2/Short1/Short2 disabled.

## Data
Used the same 19 local 4h markets with chronological 70% reference / 30% holdout splits per market. BTCUSDT_1h.csv was excluded. DOGE/DOT/UNI remained included and visible. No new-data extension was evaluated because no separate local extension dataset was available.

## Reference Aggregate
Reference: trades 1191, net PnL 5275.31, PF 1.2571, max DD 0.0946%, win rate 65.32%, positive markets 13/19.

## Holdout Aggregate
Holdout: trades 360, net PnL -69.89, PF 0.9832, max DD 0.0464%, win rate 64.72%, positive markets 8/19, negative markets 7/19, flat/no-trade markets 4/19.

## BTCUSDT Boundary
BTCUSDT holdout failed the predeclared BTC boundary: trades 47, net PnL -50.21, PF 0.8475. BTC support is useful but not sufficient; BTC failure is serious for this project.

## Weak Markets
DOGE/DOT/UNI were retained. DOGE remained strongly negative, DOT was slightly positive with very low trade count, and UNI was positive. These markets must not be removed post-result without separately predeclared validation.

## Concentration / Top Trade Contribution
Because aggregate holdout PnL is negative, top-3/top-5/top-10 concentration pass gates are not meaningful as pass evidence. For context, top 3 positive markets were UNIUSDT, AAVEUSDT, TRXUSDT with 74.98% of positive-market PnL. Top 10 positive trades were 19.86% of estimated gross positive trade PnL.

## Decision
Fail: park Long1-only; no implementation.

## Boundary
Implementation readiness remains closed / not ready. No dry-run, live trading, production, or profitability claim is made.
