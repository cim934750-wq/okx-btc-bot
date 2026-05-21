# Candidate D Mean-Reversion Synthesis Round 1

## Scope

This is a research-only synthesis and confirmation-validation plan for Candidate D from `fresh_multi_hypothesis_batch_round1`. It does not run a new backtest, run validation, fetch OHLCV, change production source code, change production parameters, optimize, sweep thresholds, restart dry-run, create live trading plans, or claim implementation readiness.

## Candidate D Summary

Candidate D is the mean-reversion / oversold bounce candidate. It is materially different from the failed Long1 family because it does not chase trend continuation, late breakouts, add-ons, or Long2-style scaling. It waits for oversold downside extension, requires a first bounce, uses no averaging down, uses no add-on entries, and exits quickly by EMA20 touch, 1.5R take profit, or an 8-candle time stop.

## Why It Deserves Confirmation

In the fresh batch holdout, Candidate D produced net PnL +3853.32, PF 1.7601, 339 trades, win rate 55.46%, average trade +11.37, median trade +12.13, and 18 positive markets out of 19. BTCUSDT was positive at +253.84 with PF 2.3689. DOGE and DOT were positive despite prior weak-market problems. Candidate D was positive across all market-family proxy groups in holdout.

## Why It Is Not Implementation-Ready

Candidate D was discovered inside a multi-hypothesis batch. A batch screen can identify a candidate for follow-up, but it is not confirmation. Candidate D may be sample dependent, rebound-regime dependent, or affected by simulator/implementation mismatch. It must be tested as a standalone frozen candidate against no-trade, passive BTC buy-and-hold, and the failed references before any dry-run discussion. A positive batch result is not implementation readiness.

## Key Risks

Oversold bounce systems can fail badly in crash regimes when oversold becomes more oversold. The stop may be too wide or too tight for some markets. The holdout sample may still be too short or regime-favorable. Family or rebound clustering could make edge look broader than it is. BTCUSDT strength is encouraging but still requires standalone confirmation. The confirmation must also check for lookahead, OHLC ambiguity, and implementation mismatch.

## Confirmation Objective

The next validation, if explicitly approved, should verify Candidate D as a standalone frozen candidate using the same exact rules, same 19-market local 4h universe, and no parameter changes. The objective is to determine whether Candidate D remains a research candidate after stricter reporting and trade-level audit, not to prepare dry-run or implementation.

## Recommendation

Create and execute a separate confirmation validation only after explicit approval. Until that confirmation passes, no-trade remains the default, the bot remains stopped, and implementation readiness remains closed.
