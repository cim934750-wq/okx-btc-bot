# Funding Feature Candidate Definition Plan Round 1

## Scope
This is a research-only frozen-definition plan. It does not run backtests, run validation, fetch new data, tune parameters, sweep thresholds, change production source code, change production parameters, modify PRs, restart dry-run, create live trading plans, revive failed candidates, or claim implementation readiness.

## Why Funding-First
The OI/funding audit found funding-rate history usable for research across 19/19 markets with 8h cadence and complete key-market visibility. Historical OI was available for 19/19 markets but constrained as 1h/base-currency aggregate history rather than exact instrument-specific historical OI via the current route. Therefore this plan uses funding as the primary feature and leaves OI diagnostic-only.

## Selected Candidate
Selected candidate: `funding_extreme_avoidance_filter_round1`.

This is a market-specific funding-rate feature gate, not a standalone trading strategy. It is designed to avoid long entries when funding is extremely positive, and to permit future long mean-reversion research entries only when funding is neutral-to-negative. It does not create entries on its own and does not revive Candidate D, K, or any prior failed path as implementation-ready.

## Frozen Funding Formula
For each market, use its own OKX USDT-swap funding series. At a 4h candle close, use only the same or most recent prior funding observation if it is no more than 4 hours old. Require 180 prior completed funding observations to compute percentile rank. Positive extreme is percentile rank >= 90. Negative extreme is percentile rank <= 10 and is diagnostic only. Long mean-reversion entries are eligible only when `current_funding_rate <= 0 OR funding_percentile_rank_prior_180 <= 50`, and they are blocked when funding is positive extreme, neutral-positive, missing, stale, or warmup-insufficient.

## Threshold Rationale
The 180-observation lookback is a structural default of about 60 days at 8h cadence. The 90/10 percentile tails are conventional decile extremes rather than optimized thresholds. The median/zero requirement for long eligibility keeps the primary candidate contrarian and crowding-aware. No alternative threshold or lookback is authorized by this plan.

## Data Constraints
Funding data is 8h cadence and maps sparsely to 4h candles. No future leakage and no silent forward-fill are allowed. OI is excluded from the primary candidate because audited historical OI is constrained; it may be reported only as diagnostic or reserved for a later second-stage plan.

## Next Step
After this plan, execute funding-feature validation only if explicitly approved, and only after a validation plan freezes the base entry/exit stream that this funding filter will gate. No dry-run, live trading, or implementation claim is authorized.
