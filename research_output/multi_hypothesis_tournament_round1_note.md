# Multi-Hypothesis Tournament Round 1 Results

## Boundary

This was a research-only tournament execution. No dry-run was restarted, no live trading was enabled, no deployment/systemd/live-loop behavior was modified, no PRs were modified, no production source code was changed, no strategy parameters were changed in production, no optimization or threshold sweep was run, no markets were removed, and no implementation-readiness claim is made.

## Executed Scope

The frozen tournament plan was inspected before execution. Only candidates with fully specified, non-invented rules were executed:

- `A no_trade_baseline`: executable baseline.
- `B passive_btc_buy_and_hold_benchmark`: executable passive benchmark using existing `data/BTCUSDT_4h.csv` and the same chronological 70/30 split convention.
- `G benchmark_only_monitoring_candidate`: executable observation-only baseline.

The active candidates `C`, `D`, `E`, `F`, and `H` were marked `not_executable_from_plan` because the plan intentionally required exact frozen rules before future validation but did not define those executable rules.

## Data Used

Existing local 4h OHLCV was inspected for the same 19-market universe: AAVE, ADA, ATOM, AVAX, BCH, BNB, BTC, DOGE, DOT, ETC, ETH, FIL, LINK, LTC, NEAR, SOL, TRX, UNI, XRP. `BTCUSDT_1h.csv` was excluded. No new OHLCV was fetched, faked, or inferred.

Passive BTC buy-and-hold was computed on the BTCUSDT 4h holdout window:

- start: `2024-02-05T04:00:00+00:00` close `43071.88`
- end: `2026-04-12T12:00:00+00:00` close `70976.19`
- return: `64.785447%`
- normalized PnL per 100,000 capital: `64785.447025`
- max close-to-close drawdown: `49.836972%`

## Result

No active trading candidate was executed because no active candidate had sufficiently frozen rules. The tournament therefore produces no active-strategy winner. No-trade remains the default, and benchmark-only monitoring remains allowed as observation only.

## Selection Decision

Decision: `all_active_candidates_not_executable_keep_no_trade_default`.

This does not prove passive BTC is a strategy candidate and does not authorize BTC-only validation. It only provides an opportunity-cost benchmark. Any future active candidate requires a separate frozen selection note and validation plan before execution.

## Implementation Readiness

Implementation readiness remains closed / not ready.
