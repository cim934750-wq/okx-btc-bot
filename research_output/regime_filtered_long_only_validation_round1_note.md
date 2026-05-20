# Regime-Filtered Long-Only Validation Round 1

## Boundary

This was a research-only validation execution of the frozen `regime_filtered_long_only_definition_plan_round1`. No dry-run was restarted, no live trading was enabled, no deployment/systemd/live-loop behavior was changed, no PRs were modified, no production source code was changed, no production strategy parameters were changed, no optimization or threshold sweep was run, no markets were removed, and no implementation-readiness claim is made.

## Frozen Rule Executed

BTCUSDT 4h regime was `risk_on` only when BTCUSDT close was above EMA200, EMA200 slope over 24 completed 4h candles was positive, and BTCUSDT close was not more than 20% below the 180-candle rolling high. Missing/warmup BTCUSDT regime was `risk_off`. Each market candle was aligned to the same or most recent prior BTCUSDT 4h closed candle. The filter blocked entries only and did not force exits. Exits, stops, sizing, and market universe were unchanged.

## Data Used

Used the same 19 local 4h markets: AAVE, ADA, ATOM, AVAX, BCH, BNB, BTC, DOGE, DOT, ETC, ETH, FIL, LINK, LTC, NEAR, SOL, TRX, UNI, XRP. BTCUSDT_1h was excluded. Chronological 70/30 split was used. No new, fake, or inferred OHLCV was used.

## Holdout Result

- Trades: `322`
- Net PnL: `-266.260475`
- PF: `0.931758`
- Max DD pct proxy: `0.317821`
- Win rate: `63.354037`
- Positive / negative / flat markets: `6 / 9 / 4`
- Actual blocked entries: `36`
- Raw blocked starter signals: `37`
- Active regime exposure: `47.001816%`

## Decision

Decision: `fail`.

Fail reasons: `aggregate_holdout_negative_or_not_positive|profit_factor_below_1|BTCUSDT_negative|basket_breadth_below_10_positive_markets|nonpositive_avg_trade_expectancy|regime_filter_blocked_entries_but_did_not_beat_no_trade`.

The candidate remains research-only and is not implementation-ready.
