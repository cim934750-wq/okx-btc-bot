# Autonomous Strategy Discovery Failure Synthesis Round 1

## Boundary
This is a research-only synthesis/postmortem for `autonomous_strategy_discovery_loop_round1`. No new backtests, validation, OHLCV fetch, source-code change, parameter change, optimization, threshold sweep, candidate tuning, dry-run restart, live planning, or implementation-readiness claim was made.

## Loop Design Summary
The autonomous loop generated 12 controls/families. It included 2 controls/benchmarks (`A_no_trade_control` and `B_passive_btc_buy_hold_benchmark`), 9 executable active candidates, and 1 non-executable active candidate (`G_btc_dominance_alt_filter`) because BTC dominance data was not available locally and no fetch was approved. The loop used the same 19 local 4h markets where applicable, excluded BTCUSDT_1h, kept BTCUSDT/DOGE/DOT/UNI visible, and used existing fetched later-data as an additional gate. No new OHLCV was fetched.

## Promotion Result
Promoted candidates: 0. Every active candidate was parked or eliminated by one or more predeclared gates: negative edge, PF below threshold, no-trade not beaten, BTC boundary failure, concentration, later-data failure, low later-data sample, or missing required data.

## Best Near Miss: K_liquidation_wick_bounce
`K_liquidation_wick_bounce` was the closest result because it was the only active candidate with positive holdout aggregate PnL: net PnL 769.17, PF 1.0843, trades 611. It still failed promotion. PF was below the minimum/preferred promotion band, BTCUSDT was negative (-14.46, PF 0.9710), concentration was excessive (top 3 market contribution 111.07%, top 10 positive trade contribution 136.36%), and existing later-data produced -35.43 net PnL with only 2 trades. This supports parked observation only, not confirmation validation or implementation.

## Interpretation
The loop does not prove automated trading is impossible. It only shows that this frozen batch of candidate families did not clear conservative research gates. That distinction matters: the correct conclusion is not that no strategy can work, but that no tested candidate currently justifies escalation beyond benchmark/no-trade observation.

## Decision
Decision: `pause_no_trade_default`. Active strategy research should pause by default. Reopening should require explicit approval and either a clearly new data source, a clearly new feature class, or a new frozen-definition inventory created before any testing.

## Final Status
No-trade / capital preservation remains the default. Benchmark-only monitoring remains allowed. Dry-run, live trading, production implementation, parameter tuning, threshold sweeping, post-result market removal, and reviving K or Candidate D directly as trading candidates remain forbidden.
