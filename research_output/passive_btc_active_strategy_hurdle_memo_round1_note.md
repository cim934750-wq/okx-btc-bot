# Passive BTC Versus Active Strategy Hurdle Memo Round 1

## Scope
This is a research-only memo for future validation gates. It does not run validation, run backtests, fetch market data, tune parameters, define new strategies, create candidate variants, revive failed candidates, change source code, change production parameters, restart dry-run, create live-trading plans, or claim implementation readiness.

## Why This Memo Exists
Recent research produced active candidates that were positive but still not promotable. The clearest example is `C_donchian_breakout_round1`: holdout PnL was `+3239.13`, PF was `1.1643`, and BTCUSDT was `+636.24`. Those are constructive observations, but passive BTC holdout PnL was `+64785.45`, beating C by `61546.32`. C also had weak breadth at 9 positive and 10 negative markets, and top-3 positive-market contribution was `67.07%`.

Positive active-strategy PnL is therefore insufficient. A strategy must also justify activity versus doing nothing, versus passive BTC opportunity cost, and versus its own complexity, execution burden, data burden, and implementation risk.

## Three Baselines
The no-trade baseline asks whether doing anything is justified at all. It remains the default when no active edge clears gates.

The passive BTC benchmark asks whether active trading is worth the opportunity cost of simply holding BTC over the same window. If passive BTC dominates by a large margin, an active strategy cannot advance unless it was predeclared to serve a different portfolio role and demonstrates materially lower drawdown, lower exposure, or lower tail risk.

The active-strategy hurdle asks whether the strategy has enough after-fee expectancy, breadth, concentration control, data quality, simplicity, and operational safety to justify more research. It is stricter than merely beating no-trade.

## Distinctions Future Work Must Preserve
Beating no-trade means active PnL is greater than zero. It does not imply passive BTC was beaten, complexity was justified, or risk was acceptable.

Beating passive BTC means the active strategy overcame a major opportunity-cost benchmark. If it underperforms passive BTC, it may at most be a caution case unless it has a predeclared defensive or diversifying role.

Producing positive expectancy means results show fee-adjusted profit factor, average/median trade quality, breadth, and risk control that look durable enough for confirmation. It is not the same as implementation readiness.

Justifying active complexity means the added data, execution, portfolio, model, or operational burden is rewarded by stronger evidence. More complicated strategies must clear higher gates.

Dry-run-ready and live-ready are separate operational decisions. A single tournament pass cannot create either status. Dry-run requires explicit approval after confirmation; live trading requires separate approval after dry-run evidence and operational review.

## C Donchian Case Study
`C_donchian_breakout_round1` was the best first-pass OHLCV tournament candidate, but it was not promoted. It beat no-trade numerically, but passive BTC dominated by `61546.32`; PF was below the preferred `1.20`; breadth was weak; and top-3 positive-market contribution showed concentration risk. C is therefore an example of `caution_positive_but_under_benchmark` or `fail_passive_btc_dominates`, not a confirmation candidate.

## Future Gate Policy
Every validation must include no-trade, passive BTC, and where feasible per-market buy-and-hold comparisons. Every positive candidate must report the passive BTC gap. Every promotion decision must state whether passive BTC was beaten or why underperformance is acceptable under a predeclared role. No implementation readiness may be claimed from a single tournament pass.

## Default Recommendation
Keep no-trade / benchmark-only monitoring as the default until a candidate clears no-trade, passive BTC, expectancy, breadth, concentration, data-quality, and complexity-adjusted gates. The bot remains stopped.
