# Taker-Flow Feature Research Plan Round 1

## Scope

This is a research-only planning and inventory note. It does not fetch data, run backtests, run validation, define an implementation-ready strategy, tune parameters, perform threshold sweeps, change production source code, change production parameters, modify PRs, restart dry-run, create live-trading plans, or claim implementation readiness.

## Current Research State

The project remains in no-trade / benchmark-only observation mode. The OHLCV-only active research chain failed or was parked: Long1-only, D2, D6, cooldown, anti-chase, regime-filtered long-only, Candidate D later-data, and the autonomous OHLCV-only discovery loop all failed to produce an implementation-ready candidate. Candidate D passed historical confirmation but failed fetched later-data validation. Funding-gated Candidate D reduced loss but still failed to create positive expectancy. Exact historical instrument-level OI could not be proven from the current OKX/ccxt route; current exact OI snapshots are unit checks only, while historical OI remains aggregate context.

No active strategy is approved. No-trade remains the default. The bot service must remain stopped.

## Why Not Another OHLCV-Only Batch

Another OHLCV-only batch is not justified immediately because the prior work already tested trend-following, breakout, mean-reversion, regime-filtered, wick-bounce, and market-family variants. The best autonomous near-miss, `K_liquidation_wick_bounce`, still failed promotion due low PF, negative BTCUSDT, concentration, and later-data weakness. Repeating OHLCV-only tests would likely become threshold shopping unless a genuinely new feature class is added.

## Why Funding And Exact OI Are Not Enough

Funding history was available and a funding extreme avoidance gate was tested, but the filtered Candidate D stream stayed negative with PF 0.0000. Funding remains observable context, not an approved trading feature.

Exact current OI was available for 19/19 markets, but exact historical instrument-level OI was not proven. Historical OI from the audited route is aggregate/ccy-level context only. It cannot support exact-instrument strategy definition from the current route.

## Next Feature Class Direction

The next research direction should focus on taker-flow / volume-imbalance / aggressive order-flow context. This is meaningfully different from pure OHLCV because it attempts to distinguish aggressive buyer-initiated and seller-initiated participation, not only candle shape or total volume. It may help identify whether breakouts, selloffs, wicks, or rebounds are supported by actual aggressive flow.

This plan does not claim the data is available. It selects feature classes for a future data-availability audit only.

## Selected Feature Classes For Next Audit

Primary selected feature class: taker buy/sell volume or taker-volume imbalance.

Secondary selected feature class: abnormal turnover / volume impulse.

These are selected because they are plausibly available from exchange public/trading-data routes, are more independent from failed OHLCV-only rules than another candle pattern, and can be audited before any strategy is defined.

## Required Data Properties

A future audit must check timestamp, symbol/instrument, taker buy volume, taker sell volume or derivable equivalent, total volume, quote volume if available, source endpoint or method, sampling interval, fetch timestamp, and raw archive/provenance path. If taker sell volume is not explicit, the audit must determine whether it can be safely derived from total volume minus taker buy volume without unit mismatch.

## Alignment Rules For A Future Audit

Any future taker-flow feature must align to 4h research candles using same/prior timestamps only. No future leakage, arbitrary forward-fill, inferred data, or synthetic values are allowed. The audit must report gaps, duplicate timestamps, timezone consistency, sampling interval, and whether aggregation from lower cadence to 4h would be required.

## Possible Future Strategy Classes If Data Is Usable

Only if data coverage and provenance are usable, future frozen plans could consider taker-flow confirmed breakout, exhaustion reversal after sell imbalance, aggressive buy continuation, liquidation-wick bounce with flow confirmation, or no-trade filters during low-flow chop. None of those strategies are defined or validated here.

## Recommendation

Create a data-availability audit plan for taker buy/sell volume and taker-volume imbalance. Do not fetch data until explicitly approved. Keep no-trade / benchmark-only monitoring as the default and keep the bot stopped.
