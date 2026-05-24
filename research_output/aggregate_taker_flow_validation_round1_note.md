# Aggregate Taker-Flow Validation Round 1

## Scope
This was a research-only validation of `aggregate_taker_flow_exhaustion_reversal_round1` exactly according to `aggregate_taker_flow_validation_plan_round1`. No new data was fetched, no production source or parameter was changed, no threshold sweep was run, and no dry-run/live behavior was touched.

## Data Used
The validation used the same 19 approved markets. OHLCV came from local 4h files for indicator warmup plus `candidate_d_later_data_fetch_validation_round1_fetched_ohlcv.csv` for the later-data validation window. Taker-flow came only from `taker_flow_data_availability_audit_round1_raw/okx_rubik_contracts_taker_volume_1h_by_ccy.jsonl`.

All taker-flow references are labeled as `aggregate_ccy_contracts_context_not_exact_instrument_flow`. The OKX Rubik data is aggregate ccy/contracts context, not exact instrument-level taker flow.

## Frozen Rules
Base stream: RSI14 <= 30, close < EMA20, current close > previous close; stop at recent 10-candle low - 0.5 * ATR14; exits at EMA20 touch, 1.5R take profit, or 8 completed 4h bars; no add-ons or averaging down.

Gate: aggregate complete 1h taker rows into the closed 4h bucket for each candidate candle. Require total taker volume > 0 and sell_imbalance_4h >= 0.20. Missing, incomplete, or below-threshold buckets block entry. No forward-fill, no partial 4h buckets, and no future 1h rows are used.

## Key Result
Ungated base stream: 35 trades, net PnL -306.518902, PF 0.309247.

Aggregate taker-flow gated stream: 0 trades, net PnL 0, PF , win rate 0.000000%, max DD 0.000000%.

## Decision
Decision: fail. The candidate must remain research-only and not implementation-ready unless all predeclared gates are passed in a future separately approved plan.
