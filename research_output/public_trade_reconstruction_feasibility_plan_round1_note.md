# Public-Trade Reconstruction Feasibility Plan Round 1

## Scope
This is a research-only feasibility plan. It does not fetch public trades, run validation, run backtests, define a strategy, create candidate variants, tune thresholds, change production source code, change production parameters, restart dry-run, create live-trading plans, or claim implementation readiness.

## Objective
The objective is to decide whether exact instrument-level taker flow can be reconstructed from public OKX trade history for the same 19 OKX USDT swap instruments. The prior OKX Rubik taker-flow audit found 1h aggregate CONTRACTS ccy-level buy/sell-like arrays for 19/19 markets, but exact instrument-level taker flow was not proven. This plan treats public trade reconstruction as a separate data-engineering feasibility problem, not as a strategy.

## Candidate Public Sources
The primary source to audit later is OKX REST `GET /api/v5/market/history-trades` for each swap `instId`. Official documentation describes it as recent instrument transactions from the last 3 months with pagination, max/default `limit=100`, rate limit 20 requests per 2 seconds by IP, fields `instId`, `tradeId`, `px`, `sz`, `side`, `source`, and `ts`, and `side` as trade side of taker. This makes reconstruction plausible only if a bounded sample verifies pagination stability, side semantics, and gap coverage.

OKX REST `GET /api/v5/market/trades` is useful only for recent public trades and sample field checks. It returns up to 500 recent public transaction records and is not a full historical source.

ccxt `fetchTrades` may be used as a wrapper or cross-check, but it does not by itself prove deeper history, stable pagination, or OKX-specific taker-side semantics. The raw OKX payload should remain the source of record.

OKX WebSocket trades can observe current live public trades but cannot reconstruct past history unless a collector was already running. It is not a historical backfill source for this audit plan.

## Side Semantics Gate
The reconstruction is valid for taker-flow research only if `side` is verified as taker/aggressor side for the exact endpoint/method used. The current documentation indicates OKX trade `side` is the trade side of taker, but the future audit must preserve raw payloads and verify this endpoint-level semantic. If side semantics cannot be proven, the audit must classify the source as `feasible_trade_flow_but_side_uncertain` or worse, and no taker-flow feature may be used.

## Reconstruction Concept
For each exact `instId`, store raw trades with timestamp, trade ID, price, size, side, source, and raw payload hash. For swaps, `sz` is contract count; notional conversion requires instrument contract metadata and should be audited separately. Reconstruct 4h buckets by grouping deduplicated trades whose UTC timestamps fall inside a completed 4h OHLCV candle interval. Do not use future trades, partially closed buckets, or forward-fill.

## Feasibility Burden
The limiting factors are likely the 3-month public history depth, 100-row page size for `history-trades`, pagination stability, high BTCUSDT row counts, storage size, and runtime/rate limits across 19 markets. A 1-year reconstruction from the native OKX history-trades route is not assumed feasible because the documented history endpoint is limited to the last 3 months.

## Minimum Future Audit
If explicitly approved, the next audit should fetch a very small bounded sample only: BTCUSDT plus DOGEUSDT or DOTUSDT, a small date window, raw archive, duplicate/gap checks, side semantic verification, closed 4h aggregation sample, and updated storage/runtime estimates. If side is missing/ambiguous, pagination is unstable, or row volume is too heavy, stop before broader fetch.

## Recommendation
Do not define a taker-flow strategy yet. Execute only a minimal public-trade reconstruction sample audit after explicit approval. Keep no-trade / benchmark-only monitoring as default and keep the bot stopped.
