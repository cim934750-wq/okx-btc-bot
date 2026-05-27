# Manual External Data Docs/Pricing Review Plan Round 1

## Purpose
This is a research-only execution plan for manual documentation and pricing review of external exact-data sources. The goal is to prepare a structured human review before any vendor API call, scrape, purchase, full backfill, sample audit, or strategy research.

This task does not call vendor APIs, scrape websites, fetch external data, download datasets, create vendor accounts, use paid API keys, run validation, run backtests, define strategies, tune thresholds, change source code, change production parameters, restart dry-run, create live plans, or claim implementation readiness.

## Why This Exists
The committed external exact-data audit plan concluded that the current local/public routes do not prove exact historical instrument-level data:

- CP1 BTC public-trade reconstruction failed under the 2,500-request cap.
- Exact historical OI was not proven from the current OKX/ccxt route.
- Aggregate taker-flow remains ccy/contracts context, not exact instrument-level flow.
- Incomplete public-trade buckets cannot support strategy research.

The next responsible step is a manual source review that verifies exact OKX swap support, data semantics, licensing, pricing, and sample access before any external data is fetched.

## Review Workflow
1. Select sources from `sources_to_review.csv` in priority order.
2. A human reviewer manually opens official documentation, pricing pages, or vendor collateral outside this plan.
3. The reviewer records evidence in `manual_evidence_template.csv` without auto-filling unverified claims.
4. Unknowns remain `unknown`; do not infer availability from marketing language.
5. Score each source using `scoring_rubric.csv`.
6. Assign one status from `review_statuses.csv`.
7. Only sources marked `likely_viable_for_sample_audit` can be proposed for a future minimal sample audit, and only after explicit approval.

## Required Manual Evidence
Each source review should capture:

- Documentation URL or document title.
- Pricing page, pricing tier, or contact-required flag.
- Data dictionary excerpt summary.
- License/archive note, including whether internal research archiving is allowed.
- Redistribution restriction note.
- Sample availability note.
- API/download/rate-limit constraints.
- Manual reviewer notes and unresolved questions.

## Go Criteria For Future Sample Audit
A source can justify a future minimal sample audit only if:

- BTC-USDT-SWAP exact support is confirmed.
- DOGE-USDT-SWAP support is either confirmed or explicitly pending after BTC.
- Taker-side semantics are confirmed for trade-flow use, or not required for the selected non-trade data type.
- Exact instrument-level OI is confirmed if OI is the target data type.
- Raw records can be archived reproducibly for internal research.
- Pricing is acceptable or a free/trial/sample route exists.
- Data can align to closed UTC 4h OHLCV buckets without forward-fill or leakage.

## Stop Criteria
Stop the path for a source if it has no exact OKX swap support, no taker-side semantics for trade-flow use, no instrument-level OI for OI use, no archive rights, unacceptable or unclear pricing, only aggregate dashboard data, no reproducible raw data, or no viable 4h alignment.

## Default
No-trade / benchmark-only monitoring remains the default. Passing this manual review does not imply implementation readiness, dry-run readiness, live readiness, or strategy viability.
