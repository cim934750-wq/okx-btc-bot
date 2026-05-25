# First-Pass OHLCV Tournament Validation Round 1

This research-only validation executed the six predeclared OHLCV tournament candidates from `first_pass_ohlcv_tournament_validation_plan_round1` using existing local 4h OHLCV only. It did not fetch market data, run dry-run/live trading, modify production source, tune thresholds, create variants, or remove markets after results.

## Data And Accounting

- Markets: same 19 local 4h markets; BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remain visible.
- Excluded data: BTCUSDT_1h, funding, OI, taker-flow, basis, private/account/order data.
- Split: 70/30 chronological reference/holdout split per market. Holdout is the primary tournament decision scope.
- Fees: 5 bps per side. Additional slippage sensitivity is reported separately.
- Sizing: 1000 USDT fixed notional per trade/position, no leverage, no averaging down.

## Holdout Result

- Best ranked candidate: C_donchian_breakout_round1 with decision `fail`, net PnL 3239.13, PF 1.1642910326917264.
- Promising for confirmation: 0.
- Caution: 0.
- Fail: 6.

No candidate is implementation-ready from this tournament. A pass, if present, only means `promising_for_confirmation` and requires separate confirmation planning before any further consideration.

## Key Markets

- BTCUSDT A_ts_momentum_ema_return_round1:82.36/247tr; B_cross_sectional_top3_round1:115.40/18tr; C_donchian_breakout_round1:636.24/37tr; D_vol_contraction_breakout_round1:22.60/39tr; E_rsi_bollinger_reversion_round1:-5.47/97tr; I_regime_filtered_trend_round1:323.18/211tr
- DOGEUSDT A_ts_momentum_ema_return_round1:810.11/181tr; B_cross_sectional_top3_round1:319.78/14tr; C_donchian_breakout_round1:-155.06/39tr; D_vol_contraction_breakout_round1:298.34/28tr; E_rsi_bollinger_reversion_round1:-183.23/89tr; I_regime_filtered_trend_round1:891.58/160tr
- DOTUSDT A_ts_momentum_ema_return_round1:-320.90/144tr; B_cross_sectional_top3_round1:-120.60/5tr; C_donchian_breakout_round1:126.16/31tr; D_vol_contraction_breakout_round1:652.17/29tr; E_rsi_bollinger_reversion_round1:-1152.80/68tr; I_regime_filtered_trend_round1:232.86/108tr
- UNIUSDT A_ts_momentum_ema_return_round1:-155.15/169tr; B_cross_sectional_top3_round1:-7.93/18tr; C_donchian_breakout_round1:337.50/23tr; D_vol_contraction_breakout_round1:-127.30/25tr; E_rsi_bollinger_reversion_round1:-529.86/62tr; I_regime_filtered_trend_round1:-256.13/130tr
