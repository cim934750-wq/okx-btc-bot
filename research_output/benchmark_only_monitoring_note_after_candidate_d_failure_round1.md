# Benchmark-Only Monitoring Note After Candidate D Failure Round 1

## Scope

This is a benchmark-only monitoring note. It does not run backtests, run validation, fetch OHLCV, tune Candidate D, change source code, change parameters, modify PR #1/#2/#3, restart dry-run, create live trading plans, generate trade signals, or claim implementation readiness.

## Current Project Status

- No active strategy is approved.
- No-trade / capital preservation remains the default.
- The previous long-only strategy chain is closed.
- Candidate D passed historical confirmation but failed fetched later-data validation.
- Candidate D is parked for implementation purposes.
- Bot service should remain stopped.
- No dry-run or live continuation is authorized.

## BTCUSDT 4h Context

Observation-only placeholder. No current BTCUSDT 4h data was fetched or analyzed in this note. BTCUSDT remains important for future benchmark context because Candidate D's later-data BTCUSDT result was negative: 1 trade, net PnL -11.62, PF 0.0.

This section must not be used to infer an entry, exit, or directional signal.

## Passive BTC Benchmark Context

Passive BTC remains an opportunity-cost benchmark only, not active strategy approval. In Candidate D's fetched later-data validation window, passive BTC was positive while Candidate D lost money. That contrast reinforces that active trading must justify activity against both no-trade and passive benchmark context.

## No-Trade Baseline

No-trade remains the default. Candidate D later-data net PnL was -174.23 and did not beat capital preservation. No active strategy currently clears the required implementation boundary.

## Volatility Regime Observation

Observation-only placeholder. No volatility regime calculation was run in this note. Future monitoring may describe volatility compression/expansion context, but it must not produce trade signals or Candidate D tuning suggestions.

## Drawdown / Rally Window Observation

Observation-only placeholder. No new drawdown or rally analysis was run. Future benchmark notes may describe passive benchmark drawdown/rally context, but not convert it into entries, exits, or readiness claims.

## Oversold-Bounce Environment Observation

Observation-only placeholder. Candidate D's later-data failure suggests the oversold-bounce environment did not support the frozen rule during the fetched window: zero take-profits, stop/time-stop dominated exits, and negative aggregate PnL. This is not permission to alter RSI, ATR, EMA, R multiple, stop, or time-stop values.

## Data Quality Notes

The most recent Candidate D later-data validation used OKX public 4h OHLCV via ccxt for the same 19 markets, saved separately in research output. BTCUSDT_1h was excluded. A one-candle initial source gap per market was documented and not filled. No current or additional OHLCV was fetched for this monitoring note.

## Possible Future Hypothesis Ideas

Future ideas may be inventoried only after explicit approval. Acceptable categories are limited to observation or planning, such as:

- benchmark-only periodic context notes
- a predeclared longer later-data observation plan
- a fresh hypothesis inventory unrelated to tuning Candidate D

No future idea may be validated without a selection note and validation plan.

## Explicit No-Action Statement

- No trade signal.
- No entry.
- No exit.
- No order.
- No dry-run restart.
- No live trading.
- No implementation readiness.
- No Candidate D tuning.

## Recommendation

Keep the bot stopped. Maintain no-trade / capital preservation as the default. Continue only benchmark-only monitoring unless the user explicitly approves a predeclared research plan.
