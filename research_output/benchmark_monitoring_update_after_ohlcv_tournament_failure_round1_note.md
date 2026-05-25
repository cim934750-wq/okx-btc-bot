# Benchmark Monitoring Update After OHLCV Tournament Failure Round 1

## Scope
This is a benchmark-only monitoring update after `first_pass_ohlcv_tournament_validation_round1` and its failure postmortem. It does not run validation, run backtests, fetch market data, tune parameters, define new strategies, create candidate variants, remove markets, change source code, change production parameters, restart dry-run, create live-trading plans, or claim implementation readiness.

## Current Project Status
The project remains in no-trade / benchmark-only observation mode. There is no active strategy approved for dry-run or live use. The bot should remain stopped.

Recent research paths are closed or parked: the OHLCV-only long-only chain failed; Candidate D failed fetched later-data validation; funding-gated Candidate D reduced losses but did not create positive expectancy; exact historical instrument-level OI was not proven from the current OKX/ccxt route; aggregate taker-flow gating produced zero trades and failed to beat no-trade; and the internet-sourced first-pass OHLCV tournament validated six candidates with zero promotions.

## OHLCV Tournament Interpretation
The tournament validated A time-series momentum, B cross-sectional top-3, C Donchian breakout, D volatility contraction breakout, E RSI/Bollinger mean reversion, and I regime-filtered trend. The result was pass `0`, caution `0`, fail `6`, promoted `0`.

`C_donchian_breakout_round1` was the best active candidate with holdout PnL `+3239.13`, PF `1.1643`, and BTCUSDT `+636.24`. It still was not promoted because passive BTC holdout PnL was `+64785.45`, beating C by `61546.32`, while C had weak breadth at 9 positive and 10 negative markets and top-3 positive-market contribution of `67.07%`.

## Why Benchmark-Only Is The Correct Default
Benchmark-only monitoring is correct because no active candidate cleared all predeclared gates, passive BTC dominated every active candidate, and no implementation-ready evidence exists. C/D/I beating no-trade numerically is not enough to justify active trading, dry-run restart, or live planning.

## Observation-Only Monitoring Scope
Allowed monitoring scope is limited to no-trade baseline status, passive BTC benchmark, BTCUSDT 4h context, broad 19-market OHLCV context, volatility-regime observation, funding context observation only, aggregate OI context only with non-instrument-level labeling, aggregate taker-flow context only with non-instrument-level labeling, data-quality notes, and research backlog notes.

Monitoring must not produce trade signals, entries, exits, dry-run readiness, live readiness, production implementation claims, failed-candidate revival, threshold tuning suggestions, or market cherry-picking.

## Reopen Conditions
Research can reopen only with explicit user approval and a clearly scoped plan such as public-trade reconstruction feasibility, external exact-instrument data audit, passive BTC versus active strategy hurdle memo, genuinely new data-source research, or a fresh feature inventory with strict predeclared gates. Any reopened path remains research-only until separately validated and approved.

## Recommendation
Keep the bot stopped. Keep no-trade / benchmark-only monitoring as the default. The most conservative next artifact is a passive BTC versus active strategy hurdle memo or continued benchmark-only status tracking, not new validation or dry-run planning.
