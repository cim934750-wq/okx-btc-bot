# Aggregate Taker-Flow Validation Failure Postmortem Round 1

## Scope
This is a research-only postmortem for `aggregate_taker_flow_validation_round1`. It does not run validation, fetch data, tune thresholds, change the base stream, change production source, restart dry-run, create live plans, or claim implementation readiness.

## Validation Result
The frozen candidate `aggregate_taker_flow_exhaustion_reversal_round1` used existing audited OKX Rubik 1h `CONTRACTS` ccy aggregate taker-flow data. All taker-flow evidence remains `aggregate_ccy_contracts_context_not_exact_instrument_flow`. It is not exact instrument-level order flow and must not be represented that way.

The ungated oversold-reversal base stream produced 35 trades, net PnL -306.52, and PF 0.3092. The aggregate taker-flow gate produced 0 trades, net PnL 0.00, and PF NA. The decision was fail.

## Why It Failed
The gate did identify a harmful base stream by blocking entries that had negative matched base PnL overall. However, it did not create a tradable edge. It blocked every executable gated entry, leaving zero trades, no positive PnL, no profit factor, no BTC/key-market evidence, and no improvement over no-trade.

Blocking bad entries is useful only if the remaining allowed set has positive expectancy. Here, no remaining allowed set existed. The outcome is therefore equivalent to no-trade, and no-trade remains the default.

## Blocked-Entry Interpretation
The validation recorded 67 blocked entries. Matched blocked base trades included 24 avoided losers totaling -443.75 and 11 missed winners totaling 137.23. The blocked base net was -306.52, which explains why the gate reduced exposure to a losing stream, but it still failed to produce an executable positive strategy.

## Status
`aggregate_taker_flow_exhaustion_reversal_round1` is parked/closed for implementation as currently frozen. It is not dry-run-ready, not live-ready, and not implementation-ready. No-trade / benchmark-only observation remains the default.
