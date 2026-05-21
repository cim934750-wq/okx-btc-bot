# Candidate D Confirmation Synthesis and Later-Data Validation Plan Round 1

## Scope

This is a research-only synthesis and planning note. It does not run new backtests, run validation, fetch OHLCV, change production source code, change production parameters, optimize, sweep thresholds, remove markets, restart dry-run, create live trading plans, or claim implementation readiness.

## Current Status

Candidate D, the mean-reversion / oversold bounce candidate, passed standalone research confirmation validation after the failed long-only strategy chain was closed. The confirmation reproduced the fresh batch Candidate D results exactly for key metrics, including holdout net PnL, PF, trade count, BTCUSDT result, and positive-market count.

Candidate D is now the leading research candidate because it is structurally different from the failed Long1-style family and because it cleared the current research confirmation gate. It remains research-confirmed only, not implementation-ready.

## Frozen Candidate D Rules

- Timeframe: 4h.
- Long entry: RSI14 <= 28, close <= EMA20 - 1.5 * ATR14, and close > previous close.
- Stop: recent 10-candle low - 0.5 * ATR14.
- Exit: EMA20 touch, 1.5R take profit, or time stop after 8 completed 4h candles.
- No averaging down.
- No add-on entries.
- No parameter changes.

## Confirmation Evidence

- Holdout: 339 trades, net PnL +3853.32, PF 1.7601, max DD 0.0492%, win rate 55.46%.
- Reference: 839 trades, net PnL +3243.00, PF 1.1629.
- BTCUSDT holdout: 19 trades, net PnL +253.84, PF 2.3689.
- DOGE/DOT/UNI remained visible: DOGE +305.79 PF 1.7331; DOT +151.54 PF 1.7586; UNI -40.73 PF 0.8909.
- Family-level holdout was positive across majors, large_alts, defi, meme_high_beta, and other.
- Exit reasons were mixed and auditable: EMA20 touch 54, take-profit 61, stop-loss 102, time-stop 122.
- Average hold time was 5.41 bars and median hold time was 6 bars.
- The implementation audit found no known lookahead or major mismatch, while documenting conservative OHLC ordering and 24 intrabar ambiguity cases.

## Why Candidate D Leads Current Research

Candidate D is not another trend-continuation or late-breakout filter layered on the failed Long1 family. It targets short-term rebounds after oversold extension, uses no add-ons, has a shorter holding profile, and did not depend on removing weak markets. It also passed BTCUSDT, no-trade, breadth, concentration, and batch-reproduction checks in the confirmation run.

## Why Candidate D Is Not Implementation-Ready

The candidate was discovered inside a multi-hypothesis batch, then confirmed on the same historical local 4h dataset and chronological split. That is meaningful research evidence, but it is not enough for implementation. It still needs validation on later/new data not used in the batch/confirmation cycle, explicit slippage/fee sensitivity where feasible, and continued no-trade and passive BTC benchmark comparison.

## Remaining Risks

- Later-data failure: the edge may not transfer beyond the current dataset.
- Crash-regime failure: oversold bounce logic can keep buying into severe downside regimes.
- Intrabar ambiguity: 24 holdout cases had multiple possible exit conditions; conservative ordering was used but execution reality may differ.
- Stop-loss frequency: 102 holdout trades exited via stop-loss, so downside behavior remains material.
- Time-stop dependence: 122 holdout trades exited by time stop, meaning a large share of trades depended on the fixed holding limit.
- Sample/regime dependence: strong holdout results may reflect a favorable rebound regime.
- Execution slippage: research fills may be cleaner than real fills around stops, targets, and EMA touches.
- Live/demo mismatch: no dry-run or live behavior has been validated for this candidate.

## Later/New-Data Validation Objective

The next validation should verify Candidate D on data not used in the batch/confirmation cycle while preserving the exact frozen rules. It must compare Candidate D against no-trade and passive BTC, keep BTCUSDT and DOGE/DOT/UNI visible, and avoid any parameter changes or post-result market selection.

## Later-Data Plan

Option A is preferred if later local OHLCV already exists and can be cleanly identified as outside the batch/confirmation period. Option B is to fetch later 4h OHLCV only after explicit approval. Option C, paper forward-test planning, is allowed only after later-data validation passes and after separate explicit approval.

## Recommendation

Do not start dry-run or implementation work. The next step is to run later/new-data validation only after this plan is reviewed and explicitly approved.
