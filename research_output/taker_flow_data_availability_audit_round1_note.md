# Taker-Flow Data Availability Audit Round 1

## Scope

This is a research-only data availability audit. It fetched only explicitly approved public taker-volume / public trade sample data for the same 19 markets. It did not fetch OHLCV, private account/order data, unrelated symbols, or funding/OI data. It did not define a strategy, run backtests, run validation, tune parameters, change production source code, restart dry-run, or create live-trading plans.

## Markets Audited

The audit used the same 19 spot-style markets mapped to OKX USDT swap instruments. BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible in all coverage tables.

## Data Sources Checked

- OKX Rubik taker-volume endpoint: `/api/v5/rubik/stat/taker-volume` with `ccy=<base>`, `instType=CONTRACTS`, and `period=1H`.
- The same Rubik endpoint with `instId=<OKX-USDT-SWAP>` added as a scope probe.
- OKX recent public trades sample: `/api/v5/market/trades` with `instId=<swap>` and `limit=20`.
- OKX public history-trades sample: `/api/v5/market/history-trades` with `instId=<swap>` and `limit=20`.
- ccxt OKX capability/method inspection for public trade/taker method support.

Raw payloads were saved under `research_output/taker_flow_data_availability_audit_round1_raw/`.

## Availability Summary

The OKX Rubik taker-volume endpoint returned 1h timestamped buy/sell volume-like arrays for 19/19 base currencies at `CONTRACTS` scope. The returned arrays are suitable for auditing taker buy/sell ratios, taker imbalance, taker delta, and abnormal turnover-like context at a ccy/contracts aggregate scope.

However, the route is not proven exact-instrument. Adding `instId` is a probe, not proof of exact OKX swap scope. Therefore the data should not be described as exact instrument-level taker flow unless a future audit proves that scope.

Public trade samples were available for all 19 swap instruments and include side, size, price, trade ID, and timestamp. That means reconstruction may be possible in principle, but only as a separate feasibility plan because full historical reconstruction could be heavy, rate-limited, and storage-intensive.

## Field And Unit Coverage

Direct endpoint arrays provide timestamp, a sell-volume-like field, and a buy-volume-like field. The audit labels these as endpoint-defined `data[1]` sell volume and `data[2]` buy volume. Units must remain endpoint-defined and are not accepted as cross-market normalized without a later source/unit audit. Quote volume is not directly provided by this route.

## Feature Computability

At the aggregate CONTRACTS ccy scope, `taker_buy_ratio`, `taker_sell_ratio`, `taker_imbalance`, `taker_delta`, and an abnormal-turnover proxy from summed taker flow are computable for all 19 markets. `range_volume_impulse` is not computable from taker-flow alone because it also requires OHLCV candle range; it remains a future plan-only formula.

## 4h Alignment

The taker-volume route is 1h. It can be aggregated into closed 4h buckets without future leakage if a future plan uses only completed lower-timeframe rows. No arbitrary forward-fill should be used. Current or incomplete 4h buckets must be excluded or handled by a predeclared rule.

## Usability Decision

Overall classification: `partially_usable_short_history`.

Reason: aggregate taker-flow context is available for all 19 markets, but exact instrument-level scope is not proven and full public-trade reconstruction was not performed. This supports a future constrained frozen-definition plan only after explicit approval; it does not authorize strategy validation, dry-run, live trading, or implementation claims.

## Recommended Next Direction

Create a research-only frozen-definition plan for one constrained aggregate taker-flow candidate, or create a separate public-trade reconstruction feasibility plan if exact instrument-level taker flow is required. Do not validate a strategy until a frozen plan is reviewed and explicitly approved. No-trade remains default.
