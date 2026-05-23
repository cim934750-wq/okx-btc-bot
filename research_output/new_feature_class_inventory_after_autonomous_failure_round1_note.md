# New Feature-Class Inventory After Autonomous Failure Round 1

## Scope
This is a research-only inventory/planning note. It does not run backtests, run validation, fetch data, change source code, change parameters, optimize, sweep thresholds, restart dry-run, create live trading plans, or claim implementation readiness.

## Why Another OHLCV-Only Batch Is Not Justified Immediately
The prior long-only chain failed, Candidate D transferred poorly into fetched later data, and `autonomous_strategy_discovery_loop_round1` generated 12 controls/families, tested 9 active candidates, and promoted 0. The best near-miss, `K_liquidation_wick_bounce`, had positive holdout net PnL but failed PF, BTCUSDT, concentration, low later-data sample, and later-data gates. That pattern says the next research question is not another candle-only variation. The next question is whether genuinely new information can explain positioning, crowding, liquidity, dominance, or event conditions that candles alone missed.

## Feature-Class Interpretation
The highest-ranked feature classes are `open_interest` and `funding_rate`. They are crypto-native, materially independent from failed OHLCV-only rules, and plausibly available from public derivatives data sources. They still require a data-availability audit before any strategy definition or validation.

`liquidation_or_long_short_squeeze_proxy` is conceptually attractive because the K near-miss tried to approximate capitulation from OHLCV wicks, but real liquidation or long/short data has higher sourcing and overfitting risk. It should not be first unless data availability is proven.

BTC/alt dominance, stablecoin liquidity, taker imbalance, and event/news filters may be useful later, but each has larger provenance, hindsight-labeling, or complexity risk. Cross-market relative strength and volatility regime classifiers are weaker next steps unless paired with new data because related OHLCV-only ideas have already failed.

## Selected Feature Classes For Possible Next Planning
At most two feature classes are selected for possible next planning: `open_interest` and `funding_rate`. This is not a validation authorization. The conservative next direction is to create a data-availability audit plan for these two classes before defining any strategy rules.

## Recommendation
Decision: `create_data_availability_audit`. Pause active strategy research unless the user explicitly approves a data audit. Keep no-trade / benchmark-only observation as the default. Do not revive Candidate D or K as trading candidates.
