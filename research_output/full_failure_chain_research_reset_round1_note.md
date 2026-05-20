# Full Failure Chain Research Reset Round 1

## Scope

This is a research-only reset / new hypothesis inventory note after the full failure chain. No backtests, validation runs, OHLCV fetches, source edits, parameter changes, optimization, threshold sweeps, PR changes, dry-run restarts, live-trading plans, or implementation-readiness claims were performed.

## Current State

The current strategy family is closed as an implementation path. The following paths have failed or are not authorized for continuation:

- Long1-only holdout failed: net PnL -69.89, PF 0.9832, BTCUSDT -50.21, BTC PF 0.8475, positive markets 8/19.
- D2 dry-run reference failed: -51.92 USDT.
- D6 early-stop dry-run reference failed: -103.78 USDT.
- Frozen 6-candle cooldown failed: net PnL -91.46, PF 0.9725, BTCUSDT -73.14, BTC PF 0.7461.
- Frozen anti-chase EMA/ATR distance filter failed: net PnL -225.26, PF 0.9445, BTCUSDT -82.62, BTC PF 0.7259.

No-trade / capital preservation remains the default because every active candidate in this chain failed to beat staying flat after fees and validation gates.

## Infrastructure vs Strategy

Server/GCP operation and service mechanics may be operationally validated, but infrastructure success is not strategy edge. A bot that can run reliably is still not worth trading if the validated strategy candidates lose money, fail BTCUSDT boundaries, or underperform no-trade. The bot service is stopped, and no dry-run/live continuation is authorized.

## Why This Strategy Family Is Closed

The family has now failed across the base Long1-only holdout and two targeted repair hypotheses. Cooldown reduced activity and commission but worsened net PnL. Anti-chase reduced a small number of entries and commission but worsened expectancy and net PnL. These results suggest the problem is not solved by small post-exit waiting or simple overextension filtering. The evidence does not support promoting any of these paths to implementation or dry-run.

## Common Failure Patterns

The repeated pattern is failed holdout transfer, BTCUSDT weakness, weak-market drag led by DOGE, isolated UNI/DOT pockets that do not rescue aggregate failure, and filters reducing activity without creating positive expectancy. Positive reference-period evidence and isolated market strength must not be overused as support when holdout and BTCUSDT fail.

## No-Trade Baseline

No-trade means no position, no strategy fees, no strategy drawdown, and capital preserved except opportunity cost. It is now the default benchmark. Future hypotheses must first prove that trading is better than preserving capital. Activity itself is not evidence.

## Hypothesis Inventory

This note inventories possible future research directions without selecting a final candidate for immediate execution. Any future path must start with a fresh selection and predeclared validation plan.

## Recommendation

Pause research and keep no-trade as default unless the user explicitly approves a fresh hypothesis inventory/selection plan. Do not reopen Long1-only, D2/D6, cooldown, or anti-chase as implementation candidates.
