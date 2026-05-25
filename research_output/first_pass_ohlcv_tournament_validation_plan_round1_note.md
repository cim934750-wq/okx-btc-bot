# First-Pass OHLCV Tournament Validation Plan Round 1

This is a research-only validation plan for the six first-pass OHLCV-testable internet-sourced candidates: A/B/C/D/E/I. It does not run validation, fetch data, tune parameters, modify production code, or authorize dry-run/live trading.

## Objective

Validate one frozen representative per eligible strategy family under a shared tournament design: same 19-market universe where feasible, same existing 4h OHLCV data, same cost assumptions, same sizing convention, same chronological split/later-data logic where applicable, and the same reporting schema.

## Included Candidates

- A_ts_momentum_ema_return_round1
- B_cross_sectional_top3_round1
- C_donchian_breakout_round1
- D_vol_contraction_breakout_round1
- E_rsi_bollinger_reversion_round1
- I_regime_filtered_trend_round1

## Frozen Rule Status

The plan uses the frozen source-inventory definitions. Minor operational ambiguities are explicitly marked in `frozen_rules_check.csv`, especially portfolio-ranking execution for B and BTC realized-volatility windowing for I. These are non-optimized structural clarifications and require explicit execution approval before validation. No thresholds may be changed during execution.

## Recommendation

The next step is to execute the first-pass OHLCV tournament only after explicit approval. The execution task must stop with a data-insufficient or rule-ambiguity report if it cannot apply the frozen rules exactly.
