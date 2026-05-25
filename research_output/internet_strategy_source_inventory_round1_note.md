# Internet Strategy Source Inventory Round 1

This research-only inventory converts the committed internet-sourced tournament plan into one simple representative candidate per A-L strategy family. It does not run validation, fetch market data, modify production code, or authorize dry-run/live trading. Internet and open-source references are used only as idea sources; no online performance claims are trusted.

## Current State

The project remains in no-trade / benchmark-only observation mode. The OHLCV-only chain, Candidate D implementation path, funding-gated Candidate D, exact-instrument OI route, autonomous OHLCV discovery loop, and aggregate taker-flow gate are closed or parked for implementation. No active strategy is implementation-ready.

## Inventory Outcome

One representative candidate was selected for each family A-L. Six candidates are first-pass eligible with existing 4h OHLCV or 4h OHLCV plus volume: A_ts_momentum_ema_return_round1, B_cross_sectional_top3_round1, C_donchian_breakout_round1, D_vol_contraction_breakout_round1, E_rsi_bollinger_reversion_round1, I_regime_filtered_trend_round1. These should still move only to a future validation-plan task, not immediate validation.

The remaining candidates are data-blocked, definition-blocked, or plan-only: F_intraday_predictability_round1, G_funding_carry_context_round1, H_basis_perp_spot_spread_round1, J_pairs_relative_value_round1, K_capped_grid_sim_round1, L_logistic_classifier_baseline_round1. These are not failed strategies; they are unavailable for first-pass tournament validation under current data and control constraints.

## Recommended Next Step

Because at least four candidates are eligible with existing 4h OHLCV, the next research step is to create a first-pass OHLCV tournament validation plan for A/B/C/D/E/I only. That plan should preserve the same 19 markets, keep BTCUSDT/DOGEUSDT/DOTUSDT/UNIUSDT visible, compare against no-trade and passive BTC, and keep all parameters frozen.
