# CP1 4h BTC Public-Trade Reconstruction Pilot Round 1

## Scope
- Checkpoint: CP1 only.
- Instrument: BTCUSDT mapped to `BTC-USDT-SWAP`.
- Endpoint used: OKX public REST `/api/v5/market/history-trades` only.
- Selected interval: `2026-05-26T08:00:00Z` to `2026-05-26T12:00:00Z` UTC, half-open `[start,end)`.
- Public trades fetched only for BTC-USDT-SWAP. DOGE, DOT, and all-19 markets were not fetched.

## Result
- Decision: `cp1_fail_incomplete_bucket`.
- Pages/requests archived: 2500 of max 2500.
- Raw archive MB: 29.646485 of max 500.
- Bucket complete: False.
- Rows inside bucket: 250000 raw, 250000 deduplicated.
- Earliest bucket trade reached: 2026-05-26T10:12:42.756000+00:00.
- Latest bucket trade reached: 2026-05-26T11:59:59.398000+00:00.

## Interpretation
CP1 did not prove 30-day feasibility. It only tests whether one completed BTC 4h bucket can be reconstructed under the CP1 cap. If the decision is not `cp1_pass_go_to_cp2_plan`, CP2 must not be executed automatically.

Side semantics rely on the committed prior minimal audit artifact, which recorded OKX documentation for `side` as the trade side of taker. No live documentation fetch was performed during CP1.

## Next Step
Allowed next step: stop_or_redesign_reconstruction_method.
Forbidden next step: do_not_advance_to_CP2.
