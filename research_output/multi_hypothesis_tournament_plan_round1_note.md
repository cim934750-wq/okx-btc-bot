# Multi-Hypothesis Tournament Validation Plan Round 1

## Purpose

This is a research-only validation plan for a controlled multi-hypothesis tournament after the full active-strategy failure chain. It does not execute validation, fetch data, change source code, change parameters, restart dry-run, create live trading plans, or claim implementation readiness.

## Current Failure Context

The prior strategy family has failed or been parked:

- Long1-only holdout: net PnL `-69.89`, PF `0.9832`, BTCUSDT `-50.21`, BTC PF `0.8475`.
- D2 dry-run reference: approximately `-51.92 USDT`.
- D6 early-stop dry-run reference: `-103.78 USDT`.
- Cooldown validation: net PnL `-91.46`, PF `0.9725`, BTCUSDT `-73.14`, PF `0.7461`.
- Anti-chase validation: net PnL `-225.26`, PF `0.9445`, BTCUSDT `-82.62`, PF `0.7259`.
- BTC-only separate gate selection: `pause_no_trade_default`.

No-trade / capital preservation remains the default. The bot service should remain stopped.

## Why A Tournament Plan Is Justified

A batch/tournament plan is acceptable only because the prior single-path chain repeatedly failed and because the candidate list, metrics, data scope, and gates are predeclared before execution. The purpose is not to optimize but to compare a small number of fixed, interpretable hypotheses against the same capital-preservation and benchmark gates.

The tournament must prevent rescue bias: candidates are defined before results, weak markets remain visible, BTCUSDT remains visible, and no candidate can be promoted because it merely loses less than a failed reference.

## Allowed Tournament Evaluation vs Forbidden Optimization

Allowed tournament evaluation:

- Uses a limited, predeclared candidate set.
- Uses fixed hypothesis definitions and frozen future-execution rules.
- Uses the same data scope and metrics across comparable candidates.
- Compares each active candidate against no-trade and failed references.
- Compares BTC-relevant candidates against passive BTC buy-and-hold.
- Produces pass/caution/fail labels and a postmortem or synthesis.

Forbidden optimization / threshold sweeping:

- Trying many parameter values and selecting the best result.
- Changing thresholds after seeing tournament output.
- Removing DOGE, DOT, UNI, BTCUSDT, or other markets after seeing results.
- Re-labeling failed candidates as implementation-ready.
- Using lower trade count alone as evidence of edge.
- Moving from tournament results directly into dry-run or live trading.

## Predeclared Candidate Set

The tournament candidate set is intentionally limited:

A. No-trade baseline.
B. Passive BTC buy-and-hold benchmark.
C. BTC-only fresh gate candidate.
D. Regime-filtered long-only candidate.
E. Volatility-regime candidate.
F. Market-family framework candidate.
G. Benchmark-only monitoring candidate.
H. Optional short/hedged framework candidate, high-risk and not immediately executable.

Any executable validation must freeze exact rules for candidates C-H before running. If a candidate cannot be specified with a fixed rule, it cannot be executed.

## Tournament-Wide Data Scope

- Same 19 local 4h markets where applicable.
- BTCUSDT remains visible.
- DOGE, DOT, and UNI remain visible.
- Chronological 70/30 split consistent with prior holdout validation.
- BTCUSDT_1h remains excluded unless a separate plan explicitly adds a different timeframe.
- No new OHLCV unless separately approved before execution.
- No fake or inferred data.
- No post-result market removal.

## Tournament-Wide Metrics

Each executable active candidate should report:

- net PnL
- profit factor
- max drawdown
- win rate
- average trade
- median trade
- trade count
- positive / negative market count
- BTCUSDT result
- DOGE / DOT / UNI result
- top 3 and top 5 market concentration
- top 10 positive trade contribution
- fee-adjusted return
- no-trade comparison
- buy-and-hold BTC comparison if BTC-relevant
- failed-reference comparison versus Long1-only holdout, D2, D6, cooldown, and anti-chase

## Selection Rules

- No candidate can pass if aggregate holdout is negative.
- No candidate can pass if PF is below `1.00`.
- BTC-relevant candidates fail if BTCUSDT is negative.
- Basket candidates fail if breadth or concentration is poor.
- Lower trade count alone is not edge.
- Beating failed Long1-only is not enough; the candidate must beat no-trade.
- A top-ranked candidate is not implementation-ready.
- Any winner requires a separate confirmation validation and postmortem/synthesis before dry-run can even be discussed.

## Multiple-Comparison Controls

- Limit the candidate set to the predeclared list.
- No threshold sweeps.
- No post-result parameter edits.
- No post-result market removal.
- Require separate confirmation after tournament.
- Require postmortem even for a winner.
- Require explicit user approval before any execution beyond this plan.

## Possible Outcomes

- All fail: keep no-trade default and bot stopped.
- One cautious candidate: create a separate validation plan; do not execute immediately.
- One strong candidate: still requires confirmation validation; no implementation claim.
- Mixed results: create synthesis; no dry-run.
- Benchmark-only remains best: continue observation-only monitoring.

## Boundary

This plan does not authorize validation execution, dry-run, live trading, source changes, parameter changes, optimization, or implementation. Implementation readiness remains closed / not ready.
