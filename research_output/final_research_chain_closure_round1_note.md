# Final Research Chain Closure Round 1

## Scope

This memo closes the failed Long1/D2/D6/cooldown/anti-chase/regime-filtered long-only research chain. It is a research-only closure artifact. It does not run a new backtest, run validation, fetch OHLCV, change source code, change parameters, optimize, sweep thresholds, modify PRs, restart dry-run, or create live trading plans.

## Full Chain Conclusion

The active long-only research chain is closed. Long1-only failed its predeclared holdout validation. D2 and D6 dry-run references were negative. The frozen 6-candle cooldown, anti-chase EMA/ATR distance filter, and BTCUSDT regime-filtered long-only candidate each failed their own predeclared gates. BTC-only immediate validation was paused because repeated BTCUSDT failures created rescue-bias risk. The multi-hypothesis tournament found no executable active candidate from its frozen plan. No-trade / capital preservation remains the default.

## Failed Candidate Sequence

- Long1-only holdout: net PnL -69.89, PF 0.9832, BTCUSDT -50.21, BTC PF 0.8475.
- D2 dry-run reference: roughly -51.92 USDT over about seven days.
- D6 early-stop dry-run reference: -103.78 USDT.
- Cooldown validation: net PnL -91.46, PF 0.9725, BTCUSDT -73.14, BTC PF 0.7461.
- Anti-chase validation: net PnL -225.26, PF 0.9445, BTCUSDT -82.62, BTC PF 0.7259.
- Regime-filtered long-only validation: net PnL -266.26, PF 0.9318, BTCUSDT -30.08, BTC PF 0.9021.

Every active candidate remained worse than no-trade on the relevant validation or reference basis.

## Why No-Trade Is The Default

No-trade means no entries, no exits, no orders, no fees, and no strategy-driven drawdown. After repeated active-candidate failures, capital preservation is the controlling baseline. A future candidate must beat no-trade after fees, pass predeclared PF/BTC/breadth/concentration gates, and survive a separate validation plan before any operational discussion can occur.

## Infrastructure Versus Strategy

GCP, systemd, and dry-run operation were useful operational/infrastructure checks. They showed that the environment can run and observe a bot workflow. They do not prove strategy edge, profitability, dry-run readiness, live readiness, or implementation readiness. Infrastructure success does not override failed strategy evidence.

## Common Failure Patterns

The chain showed failed holdout transfer, repeated BTCUSDT weakness, weak-market drag, isolated UNI strength that could not rescue aggregate/BTC failures, trade reduction without expectancy improvement, and regime filtering that reduced or blocked activity without creating edge. These are strategy failures, not deployment failures.

## Closed Scope

The following are closed from this research chain: Long1-only, D2 continuation, D6 continuation, cooldown, anti-chase, BTC-only immediate path, regime-filtered long-only, the long-only basket implementation path, dry-run/live planning, and implementation readiness.

## Allowed Scope

Allowed work is limited to no-trade default, benchmark-only monitoring, and a future fresh hypothesis only after explicit approval. Any future validation requires a fresh selection note before validation and a predeclared validation plan before execution.

## Recommendation

Do not run additional filters on the same long-only family. Keep the bot stopped. Continue with benchmark-only monitoring or pause research until a genuinely fresh hypothesis is explicitly approved.
