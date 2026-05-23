# Benchmark Monitoring Update After Exact OI Postmortem Round 1

## Scope

This is a benchmark-only monitoring update. It does not fetch data, run backtests, run validation, define a trading strategy, tune parameters, perform threshold sweeps, change source code, restart dry-run, create live-trading plans, or claim implementation readiness.

## Current Status

The project remains in no-trade / benchmark-only observation mode.

- The OHLCV-only active strategy chain failed and was closed.
- Candidate D mean-reversion was historically promising but failed fetched later-data validation and is parked for implementation purposes.
- Funding-gated Candidate D reduced later-data losses but failed to create positive expectancy, with PF 0.0000 and no-trade still preferred.
- Exact-instrument OI audit found current exact OI snapshots for 19/19 OKX swap markets, but historical exact-instrument OI was not proven.
- Historical OI from the audited route is usable only as aggregate or ccy-level context, not as instrument-level signal data.
- No active strategy is approved or implementation-ready.
- The bot should remain stopped.

## Exact OI Interpretation

Exact current OI is useful only as a point-in-time unit/provenance check. It cannot support historical validation by itself. The historical OI route is ccy-level aggregate context and cannot be treated as exact instrument history. Therefore no exact-instrument OI strategy should be defined from the current OKX/ccxt route.

Aggregate OI can remain in monitoring only if it is clearly labeled as non-instrument-level context. It must not produce entries, exits, signals, readiness claims, or exact OI strategy claims.

## Funding Feature Interpretation

Funding remains an observable market feature, but the tested funding extreme avoidance gate on the Candidate D base stream failed. It reduced losses but did not create edge. Funding thresholds, staleness rules, Candidate D rules, and market selection must not be tuned from that result.

Funding may be observed in benchmark notes only as context, not as a trade trigger.

## Observation-Only Monitoring Scope

Allowed benchmark monitoring scope:

- BTCUSDT 4h context.
- Passive BTC benchmark behavior.
- No-trade / capital preservation baseline.
- Volatility regime observations.
- Aggregate OI context only when clearly labeled non-instrument-level.
- Funding context only as observation.
- Data quality and provenance notes.
- Future hypothesis inventory notes only after explicit approval.

Monitoring must not produce trade signals, entries, exits, dry-run readiness, live readiness, production implementation claims, or tuning suggestions for failed candidates.

## Reopen Conditions

Active research may reopen only with explicit approval and one of the following:

- A genuinely new data source with clear provenance.
- An external exact-OI vendor audit that proves historical instrument-level OI with stable units.
- A strict aggregate-context-only audit plan that states the feature is not instrument-level and cannot drive entries/exits alone.
- A fresh feature inventory with predeclared constraints.

No failed path may be revived as implementation-ready.

## Recommendation

Keep the GCP/bot service stopped. Keep no-trade / benchmark-only monitoring as the default. If work continues, prefer a benchmark-only note or a plan-only aggregate-context audit, not strategy validation or dry-run planning.
