# Aggregate Taker-Flow Validation Plan Round 1

## Scope

This is a research-only validation plan for `aggregate_taker_flow_exhaustion_reversal_round1`. It does not run validation, run backtests, fetch new data, tune parameters, perform threshold sweeps, change the frozen base stream, change the frozen taker-flow threshold, change stop/exit rules, remove markets, claim exact-instrument taker flow, change production source code, restart dry-run, create live-trading plans, or claim implementation readiness.

## Validation Objective

Determine whether aggregate taker-flow exhaustion context improves the frozen 4h oversold-reversal base stream without merely reducing trade count.

The candidate uses OKX Rubik 1h `CONTRACTS` ccy aggregate taker buy/sell-like flow. The data is aggregate context only, not exact instrument-level taker flow. Every future output must label it that way.

## Frozen Candidate

Candidate: `aggregate_taker_flow_exhaustion_reversal_round1`.

Type: constrained aggregate taker-flow context gate.

Hypothesis: extreme aggregate sell-side taker imbalance after a downside move may indicate short-term exhaustion and rebound potential.

## Frozen Base Stream

The base stream is a 4h long-only research stream:

- Entry candidate when RSI14 <= 30.
- Close < EMA20.
- Current close > previous close.
- Stop = recent 10-candle low - 0.5 * ATR14.
- Exit = EMA20 touch, or 1.5R take profit, or 8 completed 4h candle time stop.
- No add-ons.
- No averaging down.
- No parameter changes.

This does not revive Candidate D as implementation-ready.

## Frozen Aggregate Taker-Flow Gate

Use complete closed 1h OKX Rubik `CONTRACTS` ccy aggregate taker data rolled into closed 4h buckets.

- `taker_buy_volume_4h` = sum of endpoint-defined buy volume over the complete closed 4h bucket.
- `taker_sell_volume_4h` = sum of endpoint-defined sell volume over the complete closed 4h bucket.
- `total_taker_volume_4h = buy + sell`.
- `sell_imbalance_4h = (sell - buy) / total_taker_volume_4h`.
- Require `total_taker_volume_4h > 0`.
- Allow long entry only when `sell_imbalance_4h >= 0.20` and the taker-flow bucket is complete and valid.

Missing or incomplete taker-flow buckets block entry. Do not forward-fill. Do not use future 1h bars. Do not use partially closed 4h buckets.

## Validation Design

A future validation, if explicitly approved, must compare:

1. Ungated base oversold-reversal stream.
2. Aggregate taker-flow-gated oversold-reversal stream.
3. No-trade baseline.
4. Passive BTC benchmark.
5. Candidate D later-data failure reference.
6. Prior autonomous loop failed references.
7. Benchmark-only observation status.

The validation must report whether any improvement is true expectancy improvement or only activity reduction.

## Data Scope

- Same 19 markets.
- Existing audited taker-flow data only.
- Existing OHLCV data only.
- BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visible.
- BTCUSDT_1h excluded.
- No new fetch in this task.
- No fake, inferred, or forward-filled data.
- No post-result market removal.

If audited taker-flow raw data is insufficient for validation coverage, execution must stop and produce a data-insufficient report.

## Required Alignment Checks

Before each 4h candidate entry, future validation must verify the relevant 1h taker-flow bucket is complete, closed, and uses only 1h rows inside that completed 4h interval. It must verify no future 1h data is used and no partial 4h bucket is used. Aggregate-context labeling must appear in outputs.

## Pass/Caution/Fail

Pass requires aggregate positive after fees, PF >= 1.10 minimum and preferably >= 1.20, no-trade beaten, improvement over ungated base stream, BTCUSDT non-negative if meaningful BTC trades exist, sufficient trade count, no excessive concentration, sufficient taker-flow coverage, improvement not merely from reducing trades, and no exact-instrument claim.

Caution applies if the result is positive but weak, low-sample, BTC-weak, concentrated, coverage-constrained, or mostly trade-count reduction.

Fail applies if aggregate performance is negative, PF < 1.00, no-trade is not beaten, performance is worse than the base stream, taker-flow mainly blocks winners, BTCUSDT is negative with meaningful trades, coverage is insufficient, concentration is excessive, or data alignment ambiguity invalidates interpretation.

## Recommendation

Do not run validation yet. The next step, if explicitly approved, is to execute `aggregate_taker_flow_validation_round1` exactly according to this plan. Implementation readiness remains closed.
