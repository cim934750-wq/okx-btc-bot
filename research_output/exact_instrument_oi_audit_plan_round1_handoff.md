=== CHATGPT HANDOFF START ===
1. run status: exact_instrument_oi_audit_plan_round1 created as research-only audit design; no OI fetch, strategy definition, validation, backtest, threshold tuning, source change, dry-run, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before this plan was 4df675a research: add funding feature validation failure postmortem.
3. commands run: verified branch/HEAD and prior audit/funding-failure inputs; wrote ten exact-instrument OI audit-plan outputs; verified files; staged only exact_instrument_oi_audit_plan_round1.* outputs; committed and pushed.
4. files changed / output paths: research_output/exact_instrument_oi_audit_plan_round1_note.md; _instrument_mapping.csv; _data_sources.csv; _required_fields.csv; _unit_checks.csv; _coverage_requirements.csv; _usability_criteria.csv; _future_strategy_classes.csv; _allowed_forbidden.csv; _handoff.md.
5. why OI audit is needed after funding failure: funding-first reduced loss but did not create edge, while prior OI history was only partially usable and not proven exact-instrument, so OI needs a data-quality audit before any strategy use.
6. exact OI audit objective: determine whether historical open interest exists for each exact OKX swap instrument, with stable units and leakage-free 4h alignment.
7. instruments and markets: same 19 markets mapped to OKX USDT swaps, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT explicitly visible.
8. data sources to audit: OKX native public REST, ccxt exact-instrument methods if supported, existing raw audit data, and third-party vendors only as a future optional source.
9. required fields and unit checks: timestamp, instId, OI value, unit/currency/contract denomination, source endpoint, fetch timestamp, raw archive/hash; checks cover contract/base/quote units, conversion feasibility, unit stability, and aggregate detection.
10. coverage and alignment requirements: 19-market coverage, overlap with prior OHLCV windows, start/end timestamps, row counts, gaps, duplicates, timezone consistency, and same/prior 4h alignment without leakage.
11. usability criteria: usable_exact_instrument_oi, partially_usable_exact_but_short_history, usable_only_as_aggregate_context, or not_usable_for_strategy_research.
12. future strategy classes unlocked: OI expansion breakout, price/OI divergence, crowded-position avoidance, OI contraction exhaustion, and squeeze-risk regime classifier, only after usable audit results and a separate frozen strategy plan.
13. what remains forbidden: OI fetch in this task, strategy definition, validation, backtests, threshold sweeps, aggregate-as-exact substitution, dry-run/live planning, and reviving closed candidates.
14. implementation readiness judgment: closed / not ready.
15. commit / push result: pending at file creation time; verify final response for actual commit and push result.
16. next recommended Codex prompt: Execute the exact-instrument OI data availability audit for the same 19 OKX swap instruments, fetching only approved public OI data and producing coverage/provenance outputs; do not define or test a strategy.
17. one-sentence conclusion: Exact-instrument OI remains a possible new feature class, but only after a stricter data audit proves the history is instrument-specific, unit-consistent, and alignable.
=== CHATGPT HANDOFF END ===
