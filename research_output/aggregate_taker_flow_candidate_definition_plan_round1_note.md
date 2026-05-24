# Aggregate Taker-Flow Candidate Definition Plan Round 1

## Scope

This is a research-only frozen-definition plan. It does not run validation, run backtests, fetch new data, tune parameters, perform threshold sweeps, change production source code, change production parameters, modify PRs, restart dry-run, create live-trading plans, or claim implementation readiness.

## Context

The project remains in no-trade / benchmark-only observation mode. Prior OHLCV-only, funding, exact-OI, and autonomous discovery paths failed or were parked. The taker-flow data availability audit found that OKX Rubik `/api/v5/rubik/stat/taker-volume` returns 1h taker buy/sell volume-like arrays for 19/19 markets, but at ccy / CONTRACTS aggregate scope. Exact instrument-level taker flow was not proven. Public trade samples are available only for reconstruction feasibility.

## Selected Candidate

Candidate name: `aggregate_taker_flow_exhaustion_reversal_round1`.

Candidate type: constrained aggregate taker-flow context gate.

Core hypothesis: extreme aggregate sell-side taker imbalance after a downside move may indicate short-term exhaustion and rebound potential. Because the data is aggregate ccy/contracts context, the taker-flow feature must be used only as a context gate and must not be described as exact instrument-level order flow.

## Frozen Base Stream

The future validation base stream is a simple 4h OHLCV oversold-reversal research stream. It is not Candidate D implementation readiness and it does not revive Candidate D as a trading candidate.

Entry candidate when all are true:

- RSI14 <= 30.
- Close < EMA20.
- Current close > previous close.

Stop and exits:

- Initial stop = recent 10-candle low - 0.5 * ATR14.
- Exit at EMA20 touch, or 1.5R take profit, or 8 completed 4h candle time stop.
- No add-ons.
- No averaging down.
- No parameter changes after this plan.

## Frozen Aggregate Taker-Flow Gate

Use only audited 1h aggregate CONTRACTS taker data rolled into complete closed 4h buckets.

Feature definitions:

- `taker_buy_volume_4h` = sum of endpoint-defined buy volume over the complete closed 4h bucket.
- `taker_sell_volume_4h` = sum of endpoint-defined sell volume over the complete closed 4h bucket.
- `total_taker_volume_4h = taker_buy_volume_4h + taker_sell_volume_4h`.
- `taker_imbalance_4h = (taker_buy_volume_4h - taker_sell_volume_4h) / total_taker_volume_4h`.
- `sell_imbalance_4h = (taker_sell_volume_4h - taker_buy_volume_4h) / total_taker_volume_4h`.

Allow long entry only when all are true:

- Valid aggregate taker-flow data exists for the complete closed 4h bucket.
- `total_taker_volume_4h > 0`.
- `sell_imbalance_4h >= 0.20`.
- The current 4h candle is already a bounce candle via base stream condition `close > previous close`.

Missing, incomplete, stale, or future taker-flow buckets block entry. Do not forward-fill. Do not use future 1h bars. Do not use a partially closed 4h bucket. Do not claim exact-instrument flow.

## Data Scope

Future validation scope is the same 19 markets, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visible. Use aggregate ccy/contracts taker-flow data only where available. BTCUSDT_1h is excluded. No market removal is allowed. No new fetch is authorized by this plan; future validation must use existing audited data if sufficient or stop/request explicit fetch approval.

## Future Comparison Design

A future validation, if explicitly approved, must compare:

1. Base OHLCV oversold-reversal stream without taker-flow gate.
2. Same stream with aggregate taker-flow exhaustion gate.
3. No-trade baseline.
4. Passive BTC benchmark.
5. Candidate D later-data failure reference.
6. Prior autonomous loop failures.

The question is whether aggregate sell-imbalance context improves the base stream beyond no-trade and beyond the ungated base stream, without merely reducing trades.

## Pass/Caution/Fail Philosophy

Pass requires positive after-fee aggregate results, PF >= 1.10 minimum and preferably >= 1.20, no-trade beaten, improvement over base stream, BTCUSDT non-negative if meaningful BTC trades exist, sufficient trade count, no excessive concentration, sufficient taker-flow coverage, and evidence that improvement is not merely trade reduction.

Caution applies to positive but weak, concentrated, low-sample, BTC-weak, or coverage-constrained results.

Fail applies if aggregate PnL is negative, PF < 1.00, no-trade is not beaten, performance is worse than base, taker-flow mainly blocks winners, BTCUSDT is negative with meaningful trades, coverage is insufficient, or concentration is excessive.

## Recommendation

Do not validate yet. The next step should be a research-only validation plan for `aggregate_taker_flow_exhaustion_reversal_round1` that preserves this exact base stream, gate, data scope, and pass/fail bands. Implementation readiness remains closed.
