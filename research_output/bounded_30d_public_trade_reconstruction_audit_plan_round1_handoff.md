# Bounded 30-Day Public-Trade Reconstruction Audit Plan Round 1 Handoff

- Plan purpose: define a staged, bounded, public-only OKX trade reconstruction audit before any larger fetch or strategy work.
- Audit scope: BTC-USDT-SWAP and DOGE-USDT-SWAP only, with DOT-USDT-SWAP listed as optional future scope requiring separate approval.
- Evidence base: minimal audit was clean for required fields and sample dedup, but only `feasible_short_sample_only`; complete 4h coverage remains unproven.
- Checkpoints: CP1 4h BTC pilot, CP2 1-day BTC/DOGE conditional pilot, CP3 7-day BTC+DOGE audit, CP4 30-day BTC+DOGE audit.
- Mandatory gates: 100% required fields, documented taker-side semantics, no conflicting duplicates, <= 1.0% benign duplicates, 0 unresolved incomplete buckets, no unexplained pagination gaps, within checkpoint runtime/request/storage budgets.
- Final feasibility labels: from `feasible_4h_only` through `feasible_30day_expandable_with_caution`, or infeasible/not recommended labels for pagination, rate limit, gap quality, storage/runtime, or overall risk.
- Implementation readiness: none. This is not dry-run-ready or live-ready.
- Next recommended prompt: approve execution of CP1 only, or approve no action and keep benchmark-only monitoring.
