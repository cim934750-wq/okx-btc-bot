# Bounded 30-Day Public-Trade Reconstruction Audit Plan Round 1

## Purpose
This is a research-only plan for a bounded 30-day public-trade reconstruction audit. It defines how a future approved execution audit would test whether OKX public trades can reconstruct complete exact-instrument taker-flow buckets for BTC-USDT-SWAP and DOGE-USDT-SWAP.

No public trades are fetched in this task. No validation, backtest, strategy definition, threshold tuning, dry-run, or live trading action is authorized.

## Evidence Base
The committed minimal public-trade reconstruction audit found a clean tiny sample for BTCUSDT -> BTC-USDT-SWAP and DOGEUSDT -> DOGE-USDT-SWAP:

- OKX public REST `/api/v5/market/trades` and `/api/v5/market/history-trades` returned required fields.
- Required fields present in the sample: `instId`, `tradeId`, `ts`, `px`, `sz`, `side`.
- OKX documentation described `side` as the trade side of the taker, accepted for sample diagnostics with documentation caveat.
- Deduplication by `instId + tradeId` produced zero duplicates in the tiny sample.
- Sample trades could be assigned to UTC 4h buckets, but every sample bucket remained `complete_bucket=False`.
- Overall feasibility class was `feasible_short_sample_only`.

This plan therefore treats complete 4h and 30-day reconstruction as unproven.

## Fixed Scope
- Public OKX REST trade data only.
- Allowed future endpoints: `/api/v5/market/history-trades` and `/api/v5/market/trades`.
- Initial instruments: `BTC-USDT-SWAP` and `DOGE-USDT-SWAP`.
- Optional plan-only third instrument: `DOT-USDT-SWAP`, not fetched unless separately approved.
- Target period for the final bounded audit: 30 full UTC calendar days.
- No all-19 market fetch is allowed in this plan.

## Staged Checkpoints
Execution must stop before each next stage unless the prior checkpoint is clean.

1. CP1 4h BTC pilot: one completed UTC 4h interval for `BTC-USDT-SWAP`.
2. CP2 1-day pilot: one full UTC day for BTC, adding DOGE only if CP1 is clean.
3. CP3 7-day bounded audit: BTC and DOGE, 42 completed 4h buckets per instrument.
4. CP4 30-day bounded audit: BTC and DOGE only, final two-market feasibility decision.

## Mandatory Stop/Go Thresholds
- Required fields `instId`, `tradeId`, `ts`, `px`, `sz`, and `side` must be present in 100% of parsed rows.
- OKX `side` must remain documented as taker/aggressor side; if uncertain, stop.
- Any conflicting duplicate for `instId + tradeId` is a hard stop.
- Benign duplicate rate after pagination and retries must be <= 1.0% of raw rows.
- Missing or incomplete buckets must be 0 unresolved buckets at every checkpoint before advancing.
- Any unexplained cursor gap inside the requested time window is a hard stop.
- Retry budget is max 3 retries per failed request; any unresolved request failure inside the target window stops the checkpoint.
- CP1 budget: max 2,500 requests, 45 minutes runtime, 500 MB raw archive.
- CP2 budget: max 20,000 requests, 6 hours runtime, 4 GB raw archive.
- CP3 budget: max 150,000 requests, 36 hours runtime, 25 GB raw archive.
- CP4 budget: max 500,000 requests, 5 days runtime, 75 GB raw archive, 10 GB processed output.
- All-19 expansion must not be recommended unless CP4 has 100% bucket completeness and projected all-19 30-day raw storage is below 300 GB with acceptable rate-limit risk.

## Raw Archive Structure
Future execution should archive exact raw response bodies under:

`research_output/bounded_30d_public_trade_reconstruction_audit_round1_raw/{checkpoint_id}/{inst_id}/{window_start}_{window_end}/page_{page_seq}_{cursor_hash}.json`

Every raw file must have a SHA256 hash in the provenance output.

## Completed 4h Bucket Proof
A bucket can be marked `bucket_complete=True` only if:

- Bucket interval is `[bucket_start_utc, bucket_end_utc)`.
- Every page needed to cover the interval was fetched.
- Pagination has no unexplained gaps.
- All rows are deduplicated.
- Bucket contains only exact matching `instId` rows.
- Required fields are present in 100% of rows.
- Side semantics remain documented as taker/aggressor side.

## Leakage Prevention
- Use only trades with timestamps inside the completed UTC 4h interval.
- Do not use future trades.
- Do not use partial buckets.
- Do not forward-fill missing trade data.
- Align reconstructed buckets to existing 4h OHLCV UTC candle boundaries.

## Output Status
This artifact set is a plan only. It creates no trade signal, no entry/exit rule, no candidate variant, no validation result, and no implementation-readiness claim.
