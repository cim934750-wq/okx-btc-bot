# First-Pass OHLCV Tournament Failure Postmortem Round 1

## Scope
This is a research-only synthesis of `first_pass_ohlcv_tournament_validation_round1`. It does not run validation, fetch data, tune thresholds, create variants, change frozen definitions, change production parameters, or authorize dry-run/live trading.

## Tournament Outcome
Six first-pass OHLCV candidates were validated: A time-series momentum, B cross-sectional top-3, C Donchian breakout, D volatility contraction breakout, E RSI/Bollinger mean reversion, and I regime-filtered trend. The tournament produced zero pass decisions, zero caution decisions, six fail decisions, and zero promotions.

The best active candidate was `C_donchian_breakout_round1` with holdout net PnL `+3239.13`, PF `1.1643`, BTCUSDT `+636.24`, DOGEUSDT `-155.06`, DOTUSDT `+126.16`, and UNIUSDT `+337.50`. It beat no-trade numerically, but it did not clear the predeclared gates.

## Why C Donchian Is Not Promoted
`C_donchian_breakout_round1` is not promoted because passive BTC holdout PnL was `+64785.45`, exceeding C by `61546.32`. C's PF of `1.1643` is above the minimum `1.10` but below the preferred `1.20`, breadth was weak at 9 positive markets and 10 negative markets, and top-3 positive-market contribution was `67.07%`. A positive active result is not enough when the simpler passive benchmark dominates by such a large margin.

## Interpretation
Beating no-trade numerically means the candidate made more than zero in the tested window. Beating passive BTC means the active strategy justified its complexity relative to holding BTC over the same holdout. Producing a tradable edge requires durable positive expectancy, breadth, risk control, clean data, and benchmark superiority. Being implementation-ready would require additional confirmation and operational approval; none of those conditions were met.

## No-Trade Default
No-trade remains the default because no candidate cleared all pass gates, passive BTC dominated every candidate, and no active edge was strong enough to justify dry-run or live planning. C/D/I beat no-trade numerically, but that is insufficient for promotion. A/B/E failed even against no-trade.

## Closed Items
The first-pass OHLCV A/B/C/D/E/I tournament is closed as currently frozen. Immediate OHLCV tournament promotion is closed. C Donchian must not be cherry-picked because it was positive. Dry-run/live planning and implementation claims remain closed.

## Allowed Next Directions
Allowed paths remain no-trade, benchmark-only monitoring, a passive BTC versus active strategy hurdle memo, public-trade reconstruction feasibility planning if explicitly approved, and external exact-instrument data audits if a genuinely new source is available. Any separate confirmation would require explicit user approval and must acknowledge passive BTC dominance.
