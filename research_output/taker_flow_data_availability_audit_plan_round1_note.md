# Taker-Flow Data Availability Audit Plan Round 1

## Scope

This is a research-only data-availability audit plan. It does not fetch data, run backtests, run validation, define a trading strategy, tune parameters, perform threshold sweeps, change production source code, change production parameters, modify PRs, restart dry-run, create live-trading plans, or claim implementation readiness.

## Current Research State

The project remains in no-trade / benchmark-only observation mode. The OHLCV-only long-only research chain failed, Candidate D failed fetched later-data validation, funding-gated Candidate D reduced loss but failed to create positive edge, exact historical instrument-level OI was not proven from the current OKX/ccxt route, and autonomous OHLCV-only discovery promoted zero candidates. No active strategy is implementation-ready and the bot service must remain stopped.

## Audit Objective

The next research question is data availability only:

Can historical taker buy/sell volume, taker-volume imbalance, or a safe equivalent be obtained for the same 19 markets, with clear units, provenance, and 4h alignment rules, without private data or future leakage?

This plan does not decide whether a taker-flow strategy works. It defines what a future approved audit must check before any strategy definition or validation.

## Markets And Instruments

The audit must preserve the same 19-market universe used in prior validation. Spot-style symbols are mapped to OKX USDT swap instruments where taker-flow data is derivative-specific. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT must remain explicitly visible in all future coverage and quality reports.

## Possible Data Sources To Check Later

A future approved audit may inspect OKX native public REST endpoints, OKX Rubik/trading-data endpoints, ccxt public methods if supported, existing local cache if present, and third-party vendors only as an optional later source. This plan does not fetch from any of them.

The future audit must classify whether the source provides direct taker buy volume, direct taker sell volume, buy/sell ratio only, taker volume ratio only, aggregated long/short taker volume, reconstructable trade-level aggressor flow from public trades, or no usable public history.

## Required Fields

Required fields include timestamp, symbol or instrument ID, taker buy volume, taker sell volume or safely derivable equivalent, total volume, quote volume if available, buy/sell ratio if only ratio exists, unit/currency/contract denomination, endpoint/method, source provenance, future fetch timestamp, and raw archive path or response hash.

If taker sell volume is derived as total taker volume minus taker buy volume, the future audit must prove the unit basis is identical. If only ratios are available, the audit must label them context-only unless volume units can be recovered.

## Derived Formulas To Audit Later

A future audit may test whether these formulas are computable, but must not validate a strategy in the audit step:

- `taker_buy_ratio = taker_buy_volume / total_taker_volume`.
- `taker_sell_ratio = taker_sell_volume / total_taker_volume`.
- `taker_imbalance = (taker_buy_volume - taker_sell_volume) / total_taker_volume`.
- `taker_delta = taker_buy_volume - taker_sell_volume`.
- `abnormal_turnover = current_volume / rolling_median_volume`.
- `range_volume_impulse = candle_range * volume` or a predeclared normalized variant.

## Alignment Requirements

Future data must align to 4h OHLCV candles without future leakage. Lower-timeframe data should be aggregated into closed 4h buckets. Same/prior timestamps may be used where relevant. No arbitrary forward-fill, synthetic data, or inferred missing values are allowed. Sparse or higher-timeframe data should be classified as not suitable for 4h strategy features unless a separate plan defines context-only usage.

The future audit must report gaps, duplicate timestamps, timezone consistency, sampling interval, market coverage, earliest/latest timestamp per market, row count, overlap with prior OHLCV reference/holdout/later windows, later-data availability, and key-market coverage.

## Usability Classes

The future audit should classify each source/market and the overall dataset as one of:

- `usable_direct_taker_flow`.
- `usable_derived_from_public_trades`.
- `usable_ratio_only_context`.
- `partially_usable_short_history`.
- `not_usable_for_research`.

## Failure Conditions

The audit fails if historical public taker buy/sell data is unavailable, only ratio data exists without volume units, history is too short, too many markets are missing, 4h alignment cannot be done safely, a private endpoint is required, trade-level reconstruction is too heavy or rate-limited, or units are ambiguous.

## Future Strategy Classes If Data Is Usable

Only after usable data is proven and a separate frozen plan is approved, future research could define taker-flow confirmed breakout, sell-imbalance exhaustion reversal, aggressive buy continuation, liquidation-wick bounce with flow confirmation, or low-flow chop no-trade filter. None are defined or validated here.

## Recommendation

Execute the taker-flow data availability audit/fetch only after explicit approval. Do not define a strategy until data usability is proven. Keep no-trade / benchmark-only monitoring as the default and keep the bot stopped.
