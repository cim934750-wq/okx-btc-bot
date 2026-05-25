=== CHATGPT HANDOFF START ===
1. run status: created public-trade reconstruction feasibility plan outputs; no public trades, market data, validation, or backtests were fetched/run.
2. branch / workspace state: research/long1-only-candidate-robustness at starting HEAD e0fdd30 before commit attempt.
3. commands run: inspected prior taker-flow audit, passive BTC hurdle memo, market mapping, source/field coverage, and official OKX/ccxt documentation; wrote plan markdown/CSV files; prepared scoped verification/staging.
4. files changed / output paths: research_output/public_trade_reconstruction_feasibility_plan_round1_note.md plus sources.csv, required_fields.csv, reconstruction_formulas.csv, market_mapping.csv, 4h_alignment_rules.csv, dedup_gap_rules.csv, storage_runtime_estimate.csv, feasibility_classes.csv, failure_stop_conditions.csv, minimal_audit_proposal.csv, allowed_forbidden.csv, handoff.md.
5. plan purpose: determine whether exact instrument-level taker flow can be reconstructed from OKX public trades before any strategy definition or validation.
6. public trade sources considered: OKX /api/v5/market/history-trades, OKX /api/v5/market/trades, ccxt okx fetchTrades as wrapper/cross-check, OKX WebSocket trades for future live collection only, and prior Rubik aggregate taker-volume as non-exact context.
7. required fields and side semantics: instId, tradeId, ts, px, sz, side, raw payload, hashes, fetch timestamp, and side proof are mandatory; side must be proven as taker/aggressor side or reconstruction is invalid.
8. reconstruction formulas: taker buy/sell volume sums sz by taker side; ratios/imbalance/delta derive from complete deduplicated 4h buckets; notional requires contract metadata before use.
9. 4h alignment / dedup / gap rules: use only completed UTC 4h intervals, no future trades, no partial buckets, no forward-fill, deduplicate by instId/tradeId or composite key, report pagination/timestamp gaps.
10. storage and runtime estimate: small samples are feasible to audit, BTCUSDT and all-19 30d/90d backfills may be heavy, and 1-year native OKX history is not assumed feasible because history-trades is documented as last 3 months.
11. feasibility classifications: feasible_exact_taker_flow, feasible_trade_flow_but_side_uncertain, feasible_short_sample_only, multiple infeasible classes, and not_recommended.
12. minimal audit proposal: future audit should start with BTCUSDT plus DOGEUSDT or DOTUSDT, tiny date/cursor window, raw archive, side verification, duplicate/gap checks, 4h aggregation sample, and stop conditions.
13. what remains allowed: plan-only use, future explicitly approved minimal sample audit, raw OKX source audit, ccxt wrapper cross-check, benchmark-only monitoring.
14. what remains forbidden: fetching trades now, validation/backtests, strategy definition, private data, full backfill without sample audit, dry-run/live restart, implementation-readiness claims.
15. implementation readiness judgment: none; feasibility plan only, not dry-run-ready and not live-ready.
16. commit / push result: pending at file creation time.
17. next recommended Codex prompt: “Execute a minimal public-trade reconstruction feasibility audit for BTCUSDT and one key market, fetching only the approved bounded sample and producing provenance/gap outputs.”
18. one-sentence conclusion: Exact taker-flow reconstruction is possible only as an audited data-engineering question, not as a strategy path yet.
=== CHATGPT HANDOFF END ===
