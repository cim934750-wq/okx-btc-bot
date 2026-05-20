# Benchmark-Only Monitoring Plan Round 1

## Purpose

This is a research-only monitoring plan after the full active-strategy failure chain and the BTC-only pause decision. It does not define a trading strategy, paper trading workflow, dry-run restart, live-readiness path, or implementation plan.

## Current Status

The active strategy family is closed as an implementation path for now. Long1-only failed the predeclared holdout validation. D2 and D6 dry-run references were negative. The frozen cooldown-after-exit hypothesis failed. The frozen anti-chase EMA/ATR distance filter failed. BTC-only was assessed under a separate-gate selection note and the selected decision was `pause_no_trade_default`.

Known failed references:

- Long1-only holdout: net PnL `-69.89`, PF `0.9832`, BTCUSDT `-50.21`, BTC PF `0.8475`.
- D2 dry-run reference: approximately `-51.92 USDT`.
- D6 early-stop dry-run reference: `-103.78 USDT`.
- Cooldown validation: net PnL `-91.46`, PF `0.9725`, BTCUSDT `-73.14`, BTC PF `0.7461`.
- Anti-chase validation: net PnL `-225.26`, PF `0.9445`, BTCUSDT `-82.62`, BTC PF `0.7259`.
- BTC-only separate-gate decision: `pause_no_trade_default`.

In all cases, no-trade remained preferred.

## Definition of Monitoring

Monitoring means observation only:

- no entries
- no exits
- no orders
- no paper trading
- no dry-run service
- no operational bot restart
- no implementation-readiness claim

Monitoring may collect benchmark context and produce research notes, but it must not create trade signals or decision automation.

## What To Monitor

The monitoring scope is limited to benchmark and context observation:

- BTCUSDT 4h trend context.
- Passive BTC buy-and-hold benchmark behavior over the observed window.
- No-trade capital preservation baseline.
- Volatility regime and compression/expansion context.
- Drawdown windows and recovery windows.
- Candidate trend/range classification observations for future hypothesis design only.
- Market breadth context if basket research is ever revisited.

## Allowed Outputs

Allowed outputs are limited to research context:

- periodic benchmark notes
- regime observations
- data quality notes
- future hypothesis ideas
- passive benchmark comparison summaries
- no-trade baseline reminders

These outputs cannot be used as entries, exits, or dry-run authorization.

## Forbidden Outputs

Monitoring is not allowed to produce:

- trade signals
- entry or exit instructions
- live-readiness claims
- dry-run-readiness claims
- production implementation claims
- strategy profitability claims
- parameter changes
- threshold sweeps
- post-result market selection

## Reopening Research

Research can be reopened only if a fresh hypothesis is proposed first. A reopened path must have a predeclared selection note, then a validation plan, then validation. The validation must compare against no-trade and, if BTC-relevant, buy-and-hold BTC. Failed paths cannot be revived as implementation candidates.

## Reporting Cadence

A conservative cadence is weekly or monthly benchmark-only notes. There should be no intraday action, no operational bot restart, and no automatic escalation from monitoring to testing.

## GCP / Bot Recommendation

Keep the GCP bot service stopped. Infrastructure success was useful, but it does not overcome strategy failure. Restarting dry-run or live services is outside this plan and remains unauthorized.

## No-Trade Baseline

No-trade remains the default because every active candidate tested in this chain failed to beat capital preservation on the relevant validation or dry-run references. Opportunity cost can be tracked through passive BTC buy-and-hold, but negative-edge activity is worse than preserving capital.

## Implementation Readiness

Implementation readiness remains closed / not ready. This plan is monitoring-only and does not move any strategy toward deployment.

## Recommended Next Action

Either pause research and keep no-trade as the default, or, if explicitly requested, create a periodic benchmark-only monitoring note template. Do not execute validation, restart dry-run, or reopen failed strategies from this plan.
