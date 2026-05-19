# no_trade_capital_preservation_baseline_plan_round1

## Scope
This is a research-only no-trade / capital preservation baseline comparison plan after the failed `long1_only_holdout_validation_round1`. It does not run a backtest, validation, OHLCV fetch, optimization, threshold sweep, source edit, PR edit, service restart, dry-run plan, or live-trading plan.

## Why This Baseline Is Needed
Long1-only is parked after failing the predeclared holdout gate: holdout net PnL -69.89, PF 0.9832, BTCUSDT holdout net PnL -50.21, BTCUSDT holdout PF 0.8475, and positive markets 8/19. D2 and D6 dry-run references were also negative: D2 roughly -51.92 USDT over about 7 days, and D6 early stop -103.78 USDT. Server/GCP operation was validated, but infrastructure success is not strategy edge.

Because active trading can lose capital, pay fees, and create drawdown, every future candidate must first justify doing anything at all. The no-trade baseline sets the conservative minimum: if a strategy cannot beat preserving capital in predeclared validation, it should not advance.

## Definition Of Doing Nothing
Doing nothing means no position, no strategy entries, no exchange trading fees from strategy activity, no strategy-driven drawdown, and capital preserved except for opportunity cost. It is not a claim that doing nothing maximizes upside; it is the baseline a candidate must beat before additional complexity or execution risk is justified.

## Comparison Baselines
Future candidates should be compared against four baselines:

1. No-trade baseline: 0 active PnL, 0 strategy fees, 0 strategy drawdown, and full capital preservation except opportunity cost.
2. Buy-and-hold BTC baseline: passive BTC exposure over the same evaluation window, used to understand opportunity cost and whether active trading improves risk-adjusted exposure.
3. Failed Long1-only baseline: the parked candidate with holdout net PnL -69.89, PF 0.9832, and BTCUSDT net PnL -50.21.
4. D2/D6 dry-run failure references: operationally informative but negative strategy references, not validation replacements.

## Minimum Evidence To Beat No-trade
A future candidate must show fee-adjusted positive holdout net PnL, PF above a predeclared threshold, controlled max drawdown, BTCUSDT non-negative if the candidate is BTC-relevant, broad enough market support for basket strategies, no excessive concentration, and no dependence on isolated outlier trades.

A reasonable default research gate for future plans is: holdout net PnL > 0, PF >= 1.10, max drawdown compensated by return and not materially worse than the parked references, BTCUSDT net PnL >= 0 with PF >= 1.05 unless the strategy is explicitly non-BTC, positive markets >= 10/19 for a 19-market basket, top 3 market contribution <= 75%, top 5 <= 100%, top 10 positive trade contribution <= 65%, and all metrics reported after fees where feasible.

## When No Strategy Remains Preferred
No strategy should remain preferred when aggregate holdout is negative, PF is below 1.00, fees consume the edge, drawdown is not compensated by return, BTCUSDT fails for a BTC-relevant strategy, market breadth is weak, or performance depends on isolated outliers. Being active is not a virtue by itself.

## Opportunity Cost Boundary
No-trade can underperform buy-and-hold in bull markets. That does not make negative-edge active trading acceptable. A strategy must justify activity through risk-adjusted improvement, not just because it creates trades. If buy-and-hold beats no-trade but active trading loses after fees or drawdown, no-trade still remains preferable to the active strategy.

## Dry-run Readiness Boundary
Dry-run can only be discussed after a candidate beats the no-trade baseline in predeclared validation, passes its own BTC/basket and concentration gates, and receives explicit user approval for a separate readiness discussion. Infrastructure success alone is not sufficient.

## Recommended Research Sequence
1. Freeze these no-trade baseline rules.
2. Choose exactly one new hypothesis.
3. Create a predeclared validation plan for that hypothesis, including no-trade, buy-and-hold, failed Long1-only, and operational-reference comparisons.
4. Run only the approved validation.
5. If the candidate fails no-trade or BTC/basket gates, park it.
6. If it passes, create a synthesis update without claiming implementation readiness.
7. Discuss dry-run only after separate explicit approval.

## Implementation Readiness Boundary
Implementation readiness remains closed / not ready. This plan does not select a strategy, authorize dry-run, authorize live trading, or claim profitability.
