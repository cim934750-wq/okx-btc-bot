# Anti-Chase EMA/ATR Distance Filter Validation Plan Round 1

## Scope

This is a predeclared validation plan only. No backtest, validation run, OHLCV fetch, source edit, parameter change, optimization, threshold sweep, PR change, dry-run restart, live-trading plan, or implementation-readiness claim is authorized here.

## Candidate Status

The candidate is research-only and not implementation-ready. Long1-only is parked. D2 and D6 dry-run references failed. The frozen 6-candle cooldown hypothesis failed and is parked. The no-trade / capital-preservation baseline remains the default until a future candidate beats it after fees and drawdown.

Known failure references:

- Long1-only holdout: -69.89 net PnL; PF 0.9832
- BTCUSDT Long1-only holdout: -50.21 net PnL; PF 0.8475
- D2 dry-run reference: -51.92 USDT
- D6 dry-run reference: -103.78 USDT
- Cooldown validation: -91.46 net PnL; PF 0.9725
- Cooldown BTCUSDT: -73.14 net PnL; PF 0.7461

## Frozen Primary Anti-Chase Rule

Primary formula for future validation:

`distance_atr = (close - ema20) / atr14`

Primary rule:

`block long entry when distance_atr > 2.0`

The rule is long-entry-only. It blocks overextended long entries. It must not change exits, stops, sizing, EMA/ATR periods, market universe, or signal construction outside this predeclared entry eligibility filter.

## Why EMA20 / ATR14 / 2.0 ATR

EMA20 is selected because the observed failure mode includes EMA20-exit losses after stretched long entries. ATR14 is a standard volatility-normalized distance denominator and is consistent with the goal of measuring extension relative to local volatility. The 2.0 ATR maximum distance is chosen as a conservative, non-optimized planning threshold intended to block only clearly overextended entries rather than broadly reshaping the strategy. It is not chosen from a threshold sweep and must not be changed after seeing validation results.

## Validation Data Scope

Future validation must use the same 19 local 4h markets with the chronological 70/30 split consistent with prior holdout validation. BTCUSDT must remain visible. DOGE, DOT, and UNI must remain visible. BTCUSDT_1h remains excluded unless a separate plan explicitly changes scope. No new OHLCV may be fetched unless separately approved. No fake or inferred data may be used.

## Pass / Caution / Fail Interpretation

Pass requires active trading to beat the no-trade baseline after fees. Aggregate holdout must be positive, PF must be at least 1.10 by default, BTCUSDT must be non-negative with PF at least 1.05 if BTC-relevant, drawdown must be controlled, overextended-entry losses must reduce, and concentration must not become excessive.

Fail is triggered by aggregate holdout negative, PF below 1.00, BTCUSDT negative, the filter only reducing trades/fees without improving expectancy, gains relying on isolated outliers, DOGE/DOT/UNI being hidden or removed, or threshold behavior looking cherry-picked.

## Secondary Sensitivity Boundary

Only after the primary validation result is recorded may a separate sensitivity study be proposed. It must not be used to reselect the primary threshold after the fact. Secondary sensitivity is allowed only as a robustness description, not optimization.

## Recommendation

Proceed next by executing `anti_chase_validation_round1` exactly from this frozen plan only if explicitly approved. Until then, no-trade remains the default and implementation readiness remains closed.
