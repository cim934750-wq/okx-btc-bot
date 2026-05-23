# Funding Feature Validation Round 1

## Scope
This was a research-only validation of `funding_extreme_avoidance_filter_round1` according to `funding_feature_validation_plan_round1`. No dry-run or live trading was started, no new data was fetched, no production source or parameter was changed, and no threshold/base-stream change was made.

## Data Used
The validation used the same 19 approved 4h markets. The base OHLCV stream used local 4h files for indicator warmup plus `candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv` for the later-data validation window. Funding came only from `oi_funding_data_availability_audit_round1_raw/funding_history.csv`, with 19/19 markets available at 8h cadence from 2026-02-19T16:00:00+00:00 to 2026-05-23T08:00:00+00:00.

## Frozen Rules
The base stream is Candidate D research baseline only: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, close > previous close, initial stop at recent 10-candle low - 0.5 * ATR14, exits at EMA20 touch, 1.5R take profit, or 8 completed 4h candles. The runner reproduced the known Candidate D later-data result exactly before applying the funding gate.

The funding gate is market-specific. It uses the same or prior funding timestamp only, max 4h staleness, 180 prior funding observations, and no arbitrary forward-fill. Per the frozen plan, positive extreme and neutral-positive funding states block long entries; valid neutral-to-negative states allow entries. Missing, stale, and warmup-insufficient funding block entries. Negative extreme is diagnostic only.

## Key Result
Base Candidate D later-data result reproduced at -174.234660 net PnL, PF 0.131326, 15 trades. The funding-gated stream improved the loss to -126.242029 net PnL with PF 0.000000 across 7 trades, but it remained negative and did not beat no-trade.

## Decision
Decision: fail. The funding gate reduced damage versus the failed base later-data run, but the filtered candidate remained negative after fees, had PF below 1.00, did not beat no-trade, and therefore does not justify dry-run, live trading, or implementation readiness.
