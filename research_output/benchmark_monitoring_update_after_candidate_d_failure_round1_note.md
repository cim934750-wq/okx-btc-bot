# Benchmark-Only Monitoring Update After Candidate D Failure Round 1

## Scope

This is a benchmark-only monitoring update after Candidate D later-data failure. It does not run backtests, run validation, fetch OHLCV, tune Candidate D, change RSI/ATR/EMA/R/stop/time-stop values, change source code, change parameters, modify PR #1/#2/#3, restart dry-run, create live trading plans, or claim implementation readiness.

## Current Strategy State

The prior long-only strategy chain is closed. Candidate D was the first promising research-only candidate after that closure: it passed historical confirmation, but it failed fetched later-data validation. Candidate D is now parked for implementation purposes. No active strategy is implementation-ready.

No-trade / capital preservation remains the default. Benchmark-only monitoring remains allowed as observation only. The bot should remain stopped.

## Candidate D Interpretation

Candidate D's historical confirmation was meaningful but did not transfer to fetched later data. The later-data failure was serious: net PnL -174.23, PF 0.1313, BTCUSDT -11.62, zero take-profits, and stop/time-stop dominated exits. This blocks dry-run or live escalation.

Candidate D may only remain as an archived research hypothesis or as part of a longer later-data observation plan if explicitly approved and predeclared. It must not be tuned or promoted from the current evidence.

## Benchmark-Only Monitoring Scope

Monitoring should observe context only:

- BTCUSDT 4h context.
- Passive BTC buy-and-hold benchmark behavior.
- No-trade / capital preservation baseline.
- Volatility regime.
- Drawdown and rally windows.
- Oversold bounce environment as observation only.
- Whether future market structure appears suitable for mean-reversion research observation.

Monitoring must not produce signals, entries, exits, orders, paper trading, dry-run readiness, live readiness, implementation claims, or Candidate D tuning suggestions.

## Reopen Conditions

Research can reopen only with explicit user approval and either a fresh hypothesis or a longer-data observation plan. Any future path must freeze rules before testing, define no-trade comparison, avoid parameter tuning, and create a validation plan before validation.

## Recommendation

Keep the GCP/bot stopped. Continue no-trade as default. Use benchmark-only monitoring if context is needed, but do not restart trading workflows or promote Candidate D.
