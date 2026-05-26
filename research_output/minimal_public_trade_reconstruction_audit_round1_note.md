# Minimal Public-Trade Reconstruction Audit Round 1

## Scope
This is a research-only data availability, semantics, provenance, and feasibility audit. It fetched only tiny bounded OKX public trade samples for BTCUSDT and DOGEUSDT mapped to `BTC-USDT-SWAP` and `DOGE-USDT-SWAP`. It did not fetch private data, account data, order data, WebSocket data, OHLCV, all 19 markets, or a full history backfill. It did not define or validate a trading strategy.

## Sources Used
The audit used OKX public REST `/api/v5/market/trades` with `limit=50` for recent field checks and `/api/v5/market/history-trades` with `type=2`, timestamp `after` cursors, and `limit=100` for a two-page bounded history pagination probe. Raw payloads were archived under `research_output/minimal_public_trade_reconstruction_audit_round1_raw/`.

## Markets
- BTCUSDT -> `BTC-USDT-SWAP`
- DOGEUSDT -> `DOGE-USDT-SWAP`

DOGEUSDT was selected as the one key market because the existing mapping was high-confidence and it is a required visible key market in prior reports.

## Field And Side Semantics
The bounded sample returned required fields `instId`, `tradeId`, `ts`, `px`, `sz`, and `side` for the sampled rows. OKX documentation describes `side` for public trades as the trade side of taker. This is sufficient for sample-only taker-flow reconstruction diagnostics, but broad reconstruction remains unproven until complete interval coverage, pagination stability, and runtime/storage burden are audited.

## Dedup And Gaps
Trades were deduplicated by `instId + tradeId`. Overlap duplicates can occur when recent and history samples intersect; this is expected and must be removed before aggregation. Timestamp/gap checks were performed only on the bounded sample and do not prove full 4h interval coverage.

## 4h Aggregation Sample
Sample trades were assigned to completed UTC 4h bucket boundaries, and sample taker buy/sell volumes and ratios were computed with `complete_bucket=False`. These values are diagnostics only and must not be used as strategy features because the bounded sample does not cover complete 4h buckets.

## Feasibility Decision
Overall class: `feasible_short_sample_only`.

Reason: exact instrument public trade rows with required fields and documented taker-side semantics are available in a tiny sample, but broad history depth, rate-limit burden, storage burden, stable pagination over complete 4h intervals, and all-market coverage remain unproven. This does not authorize strategy validation or full backfill.

## Recommended Next Step
If explicitly approved, create a bounded 30-day reconstruction audit plan with staged checkpoints: first one full 4h interval, then one day for BTCUSDT and DOGEUSDT, then a narrow 7-day check before any 30-day run. Stop immediately if side semantics, pagination, storage/runtime, or complete bucket coverage fails.
