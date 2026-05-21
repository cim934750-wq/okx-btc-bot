# Candidate D Later-Data Failure Postmortem Round 1

## Scope

This is a research-only postmortem/synthesis after `candidate_d_later_data_fetch_validation_round1`. It does not run new backtests, run validation, fetch OHLCV, change source code, change parameters, optimize, sweep thresholds, tune Candidate D, remove markets, restart dry-run, create live trading plans, or claim implementation readiness.

## Candidate D Status

Candidate D, the mean-reversion / oversold bounce candidate, previously passed historical confirmation validation but failed the fetched later-data gate. The conservative status is: `parked_for_implementation_purposes_research_only_needs_longer_later_data_window_if_explicitly_approved`.

This means Candidate D is not dry-run-ready, not live-ready, and not implementation-ready. It may only remain as a research-only hypothesis if a longer later-data or forward-data observation plan is explicitly approved in advance.

## Historical Confirmation vs Later-Data Failure

Historical confirmation was strong: 339 holdout trades, net PnL +3853.32, PF 1.7601, max DD 0.0492%, win rate 55.46%, BTCUSDT +253.84 with PF 2.3689, DOGE +305.79, DOT +151.54, UNI -40.73, and positive family-level results.

Fetched later data was the opposite: 15 trades, net PnL -174.23, PF 0.1313, max DD 0.1742%, win rate 13.33%, BTCUSDT -11.62 with PF 0.0, DOGE -18.12, DOT -9.89, UNI no trades, and no active family group positive.

The difference is not a mild degradation. It is a transfer failure from the historical confirmation window into newly fetched later data.

## Why The Failure Is Serious

- Aggregate later-data PnL was negative after fees.
- PF was 0.1313, far below the minimum 1.00 fail threshold and the 1.10/1.20 research gates.
- No-trade was better by 174.23.
- BTCUSDT had one meaningful trade and it was negative.
- Take-profit count was zero.
- Exits were dominated by stop-loss and time-stop: 6 stop-loss exits and 8 time-stop exits out of 15 trades.
- Passive BTC was strongly positive over the same benchmark window while the strategy lost.
- Base result was already negative and extra slippage/fees worsened it to -204.08 at 10 bps per side.

## Possible Explanations Without Tuning

These explanations are diagnostic only and must not be used to tune parameters after the fact:

- Later window regime mismatch: the oversold bounce pattern that worked historically may not have fit the short fetched window.
- Current market structure failure: oversold rebounds did not reliably reach EMA20 or 1.5R.
- Small sample: 15 trades is a low-count later-data window, but the result was decisively negative rather than merely inconclusive.
- Stop/time-stop behavior: losses came from stop-loss exits and time stops, while take-profit was never reached.
- Fee/slippage fragility: because the base result was negative, any execution friction made the failure worse.
- BTC weakness: BTCUSDT failure blocks advancement for a BTC-relevant project even though the sample was small.

## Boundary

No parameter changes are allowed from this postmortem. Do not change RSI, ATR, EMA, R multiple, stop, time stop, market universe, or exit behavior in response to this failure. Do not remove DOGE/DOT/UNI or any other market after seeing results.

## Recommendation

Park Candidate D for implementation purposes. Do not advance to dry-run. Keep no-trade / capital preservation as the default. If research continues, the only acceptable Candidate D continuation is a predeclared longer later-data / forward-data observation plan with frozen rules and explicit approval before execution.
