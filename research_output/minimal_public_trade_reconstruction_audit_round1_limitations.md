# Minimal Public-Trade Reconstruction Audit Round 1 Limitations

- This was a tiny bounded sample, not a full history reconstruction.
- Only BTCUSDT and DOGEUSDT were sampled; the other 17 markets were not fetched.
- `/api/v5/market/history-trades` is documented as last 3 months, so 1-year native reconstruction is not assumed feasible.
- The sample does not prove complete 4h bucket coverage.
- The 4h aggregation output is diagnostic only and explicitly marks buckets incomplete.
- Side semantics are based on OKX documentation stating public trade `side` is trade side of taker; no independent order-book replay was performed.
- Swap `sz` is contract count; quote/base notional reconstruction requires separate contract metadata checks.
- No strategy, candidate, threshold, validation, dry-run, or live plan is created by this audit.
