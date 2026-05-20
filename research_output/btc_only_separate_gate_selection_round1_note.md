# BTC-Only Separate Gate Selection Round 1

## Scope

This is a research-only BTC-only separate-gate selection note after the full Long1/D2/D6/cooldown/anti-chase failure chain. No backtests, validation runs, OHLCV fetches, source edits, parameter changes, optimization, threshold sweeps, PR changes, dry-run restarts, live-trading plans, or implementation-readiness claims were performed.

## Failure Context

The current strategy family is closed as an implementation path:

- Long1-only holdout failed: net PnL -69.89, PF 0.9832, BTCUSDT -50.21, BTC PF 0.8475, positive markets 8/19.
- D2 dry-run reference failed: -51.92 USDT.
- D6 early-stop dry-run reference failed: -103.78 USDT.
- Cooldown validation failed: net PnL -91.46, PF 0.9725, BTCUSDT -73.14, BTC PF 0.7461.
- Anti-chase validation failed: net PnL -225.26, PF 0.9445, BTCUSDT -82.62, BTC PF 0.7259.

No-trade / capital preservation remains the default.

## Why BTC-Only Cannot Rescue the Basket

BTC-only cannot be used to reinterpret or rescue the failed 19-market basket. BTCUSDT failed inside Long1-only holdout, failed under cooldown, and failed under anti-chase. Narrowing to BTC after seeing basket failure would create rescue bias unless a completely separate BTC-only hypothesis is defined before any validation.

## BTCUSDT Failure Interpretation

BTCUSDT failure is serious because BTC is central to the project. The repeated BTCUSDT results are not merely a weak-market side note:

- Long1-only BTCUSDT holdout: -50.21, PF 0.8475
- Cooldown BTCUSDT: -73.14, PF 0.7461
- Anti-chase BTCUSDT: -82.62, PF 0.7259

A BTC-only path would have to start from a new premise and a stricter separate gate, not from confidence in the failed family.

## Assessment

BTC-only is not justified for immediate validation now. The strongest conservative decision is `pause_no_trade_default`. A BTC-only path remains theoretically allowable only if the user explicitly approves a separate predeclared plan later. That plan must include no-trade and buy-and-hold BTC comparisons, not just active strategy PnL.

## No-Trade and Buy-and-Hold Boundary

No-trade is the default because all active candidates lost after fees or failed gate criteria. For BTC-only, opportunity cost matters: no-trade may underperform buy-and-hold BTC in bull markets, but negative-edge active trading is still worse than preserving capital. A BTC-only candidate must be compared both against no-trade and passive BTC buy-and-hold over the same window on a risk-adjusted basis.

## Decision

Selected decision: `pause_no_trade_default`.

BTC-only is not selected for validation now. No implementation readiness, dry-run readiness, live-trading readiness, or profitability claim is made.

## Recommendation

Keep no-trade as default and pause. If BTC-only is reconsidered later, first create a separate BTC-only validation plan with frozen candidate definition, data scope, no-trade comparison, buy-and-hold BTC comparison, metrics, pass/caution/fail bands, and forbidden work. Do not run validation until that plan is explicitly approved.
