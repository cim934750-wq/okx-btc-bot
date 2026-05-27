# CP1 Public-Trade Reconstruction Failure Postmortem Round 1 Handoff

- CP1 result: `cp1_fail_incomplete_bucket`.
- Bucket: `2026-05-26T08:00:00Z` to `2026-05-26T12:00:00Z` for `BTC-USDT-SWAP`.
- Clean checks: required fields 100%, side semantics documented with caveat, duplicate count 0, conflicting duplicate count 0.
- Failure: 2,500-request cap exhausted before bucket start; earliest reached trade `2026-05-26T10:12:42.756000+00:00`.
- Coverage gap: approximately 2h12m42.756s missing from the bucket start to earliest reached trade.
- Feature interpretation: buy/sell volumes and imbalance are diagnostic only because `bucket_complete=false`.
- CP2 status: blocked; do not execute CP2, DOGE, DOT, 7-day, 30-day, or all-19 public-trade reconstruction.
- Default: no-trade / benchmark-only monitoring remains correct.
- Implementation readiness: none; not dry-run-ready; not live-ready.
