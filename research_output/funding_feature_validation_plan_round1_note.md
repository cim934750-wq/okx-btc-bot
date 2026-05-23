# Funding Feature Validation Plan Round 1

## Scope
This is a research-only predeclared validation plan for `funding_extreme_avoidance_filter_round1`. It does not run validation, run backtests, fetch new data, tune parameters, sweep thresholds, change production source code, change production parameters, modify PRs, restart dry-run, create live trading plans, or claim implementation readiness.

## Validation Objective
Validate whether a market-specific funding-rate crowding filter can improve a frozen long mean-reversion base stream by avoiding long entries during extremely positive or otherwise non-contrarian funding states. The key question is whether funding-based avoidance improves robustness versus the base Candidate D stream, especially on fetched later-data where Candidate D failed, without merely reducing trade count.

## Frozen Base Stream
The base stream for this validation plan is Candidate D mean-reversion / oversold bounce, used only as a research baseline stream and not revived as implementation-ready. The base stream is 4h long-only: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, and close > previous close. Initial stop is recent 10-candle low - 0.5 * ATR14. Exits are EMA20 touch, 1.5R take profit, or time stop after 8 completed 4h candles. No averaging down, no add-on entries, no parameter changes.

## Frozen Funding Gate
For each base-stream candidate long entry, use that market's audited OKX USDT-swap funding history. Use only the same or most recent prior funding timestamp at or before the 4h candle close, with max staleness 4h. Require 180 prior completed funding observations before computing percentile rank. Compute `funding_percentile_rank_prior_180` by comparing the current available funding rate against the prior 180 observations, excluding the current funding value from the reference window.

Round 1 entry eligibility is intentionally strict and contrarian: allow the base long entry only when funding data is valid, not warmup-insufficient, not stale, not missing, funding percentile < 90, and the funding state is neutral-to-negative: current funding rate <= 0 OR percentile <= 50. Block when funding percentile >= 90, neutral-positive, missing, stale, or warmup-insufficient. Negative funding extreme <= 10th percentile is diagnostic only and does not alter sizing, exits, stops, or entry priority.

## Comparison Design
Future validation must compare two streams over identical market/time windows: base Candidate D without funding filter and Candidate D gated by `funding_extreme_avoidance_filter_round1`. Reports must separate trade-count reduction from expectancy improvement by showing blocked entries, missed winners, avoided losers, and bucket-level outcomes. No-trade remains the capital-preservation gate. Passive BTC remains an opportunity-cost benchmark only.

## Data Scope
Use the same 19 approved markets: AAVEUSDT;ADAUSDT;ATOMUSDT;AVAXUSDT;BCHUSDT;BNBUSDT;BTCUSDT;DOGEUSDT;DOTUSDT;ETCUSDT;ETHUSDT;FILUSDT;LINKUSDT;LTCUSDT;NEARUSDT;SOLUSDT;TRXUSDT;UNIUSDT;XRPUSDT. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT must remain visible. Use existing audited funding data only for this plan and existing OHLCV/fetched later-data windows where available in future validation. BTCUSDT_1h is excluded. OI is diagnostic-only and must not affect eligibility. No fake, inferred, forward-filled, or newly fetched data is authorized by this plan.

## Pass/Fail Philosophy
A pass requires real edge improvement, not just lower activity. The filtered candidate must beat no-trade, improve over the base Candidate D later-data result, maintain adequate funding coverage, avoid excessive concentration, and remain BTCUSDT-safe if there are meaningful BTC trades. A top research pass would still require later synthesis and is not implementation-ready.

## Next Step
Execute funding-feature validation only after explicit approval. The next task should run exactly this frozen comparison, produce coverage and blocked-entry audits, and avoid any threshold or base-stream changes regardless of outcome.
