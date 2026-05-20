# Regime-Filtered Long-Only Failure Postmortem Round 1

## Scope

This is a research-only failure postmortem for `regime_filtered_long_only_validation_round1`. It does not run a new backtest, change source code, tune thresholds, restart dry-run, or create any live trading plan.

## Candidate Under Review

The frozen candidate used BTCUSDT 4h as the regime anchor. Entries were allowed only when BTCUSDT close was above EMA200, EMA200 slope over 24 completed 4h candles was positive, and BTCUSDT close was not more than 20% below the 180-candle rolling high. Missing or warmup anchor state was treated as risk_off. The filter blocked entries only and did not force exits. Exits, stops, sizing, market universe, and DOGE/DOT/UNI visibility were unchanged.

## Validation Result

The holdout failed the predeclared gate. Across the same 19 local 4h markets, the candidate produced 322 trades, net PnL -266.26, profit factor 0.9318, win rate 63.35%, average trade -0.83, 6 positive markets, 9 negative markets, and 4 flat/no-trade markets. The result was worse than no-trade and worse by net PnL than the failed Long1-only holdout, D2, D6, cooldown, and anti-chase references.

## Why The Regime Filter Failed

The risk_on filter reduced activity but did not create positive expectancy. Holdout risk_on exposure was 47.00%, with 37 raw blocked starter signals and 36 actual blocked entries. This was not enough to turn the candidate positive: aggregate holdout remained negative and profit factor stayed below 1.0. Blocking entries is only useful if the remaining trades improve expectancy; here the remaining basket still failed.

## BTCUSDT Interpretation

BTCUSDT is a serious failure point because the regime anchor itself is BTCUSDT 4h. BTCUSDT holdout produced 44 trades, net PnL -30.08, and profit factor 0.9021. A BTC-relevant candidate cannot advance when BTCUSDT remains negative under its own anchor regime.

## DOGE/DOT/UNI Interpretation

DOGE remained a visible weak market, with net PnL -287.14 and PF 0.3586. DOT was slightly positive at +7.81 with PF 1.1487, but only on 3 trades, so it is not a rescue signal. UNI was strong at +436.62 with PF 2.2267, but isolated strength cannot rescue negative aggregate performance, BTCUSDT failure, and weak basket breadth.

## No-Trade And Buy-And-Hold Interpretation

No-trade remains preferred because the active candidate lost -266.26 versus no-trade at 0. Passive BTC buy-and-hold returned 64.7854% over the holdout window with a 49.8370% max close-to-close drawdown. That benchmark is an opportunity-cost reference only; it does not approve the active strategy. The active candidate first needed to beat no-trade and its own predeclared gates, and it did not.

## Closed Items

The following are closed as implementation or dry-run candidates from this chain: Long1-only base candidate, D2/D6 dry-run continuation, cooldown, anti-chase, BTC-only immediate path, regime-filtered long-only candidate, long-only basket implementation path, dry-run/live planning, and implementation readiness.

## Allowed Remaining Work

Allowed work is limited to no-trade default, benchmark-only monitoring, and a fresh hypothesis only after a new selection note and predeclared validation plan. A possible non-long-only or non-price framework may be considered only with a separate predeclared gate. Another immediate long-only filter test is not recommended from this evidence.

## Recommendation

Park the regime-filtered long-only candidate. Keep no-trade as the default. Do not test another long-only filter immediately. Move only to benchmark monitoring, pause, or create a fresh hypothesis inventory if explicitly approved.
