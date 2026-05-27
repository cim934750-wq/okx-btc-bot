# CP1 Public-Trade Reconstruction Failure Postmortem Round 1

## Purpose
This research-only postmortem explains why CP1 failed, why CP2 must not be executed, and what bounded redesign options remain. It keeps the project in no-trade / benchmark-only observation mode.

## CP1 Summary
CP1 attempted to reconstruct one complete BTC-USDT-SWAP public-trade bucket for `2026-05-26T08:00:00Z` to `2026-05-26T12:00:00Z` using OKX public REST `/api/v5/market/history-trades` with `type=2`, `limit=100`, and backward pagination from the bucket end.

The audit fetched and archived 2,500 exact OKX JSON response bodies, producing 250,000 parsed bucket rows. Required fields were present in 100% of rows, side semantics were documented with caveat from the prior committed local artifact, and deduplication was clean with zero duplicates and zero conflicting duplicates.

## Failure
CP1 failed because pagination did not reach the bucket start within the 2,500-request cap. The earliest reached trade was `2026-05-26T10:12:42.756000+00:00`, leaving approximately 2h12m42.756s from the bucket start unproven. Because the full `[08:00, 12:00)` interval was not covered, `bucket_complete=false`, unresolved gap risk is true, and the computed taker-flow values are diagnostic only.

## Why CP2 Is Blocked
CP2 would require reconstructing six completed 4h buckets for one full UTC day, and potentially adding DOGE only after CP1 is clean. Since one BTC 4h bucket could not be proven under the CP1 cap, CP2 is not justified. Executing CP2 would multiply an unresolved pagination/coverage problem and risk producing incomplete data at larger scale.

## Correct Interpretation
- Public trade fields exist.
- The tiny sample and CP1 fetched rows were structurally clean.
- Exact taker/aggressor side remains accepted only with documentation caveat.
- Full 4h BTC bucket reconstruction failed under current cap.
- Exact instrument-level taker-flow remains unproven for strategy research.
- No strategy, validation, dry-run, live trading, or implementation readiness follows from CP1.

## Recommended Direction
The conservative default is to stop public-trade reconstruction expansion and keep benchmark-only monitoring. Optional bounded research can be limited to an endpoint/pagination mechanics probe, a request/cost estimate memo, or an external exact-data audit plan. CP2, DOGE/DOT/all-19 expansion, and strategy validation from incomplete public-trade buckets remain closed.
