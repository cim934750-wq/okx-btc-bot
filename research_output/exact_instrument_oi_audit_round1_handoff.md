=== CHATGPT HANDOFF START ===
1. run status: exact_instrument_oi_audit_round1 executed as data availability audit only; no strategy definition, backtest, validation, OHLCV fetch, private data fetch, tuning, source change, dry-run, or live planning.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before audit was 56ed1e3 research: add exact instrument OI audit plan.
3. commands run: verified branch/HEAD and plan mapping; fetched approved public OI endpoint data; saved raw payloads; wrote coverage/provenance/usability outputs; ran sanity checks; staged only audit outputs/script; committed and pushed.
4. files changed / output paths: research/exact_instrument_oi_audit_round1.py; research_output/exact_instrument_oi_audit_round1_note.md; _instrument_mapping.csv; _fetch_log.csv; _coverage.csv; _unit_checks.csv; _alignment_assessment.csv; _gaps_duplicates.csv; _usability_decision.csv; _data_paths.csv; _limitations.md; _handoff.md; raw payloads under research_output/exact_instrument_oi_audit_round1_raw/.
5. instruments audited: same 19 OKX USDT swap instruments, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visible.
6. data sources / endpoints used: OKX native current open-interest endpoint by exact instId; OKX native Rubik contracts open-interest-volume by ccy and ccy+instId; ccxt OKX fetch_open_interest_history 1h for comparison.
7. exact OI availability summary: current exact instrument OI was available for 19/19 markets, but historical exact-instrument OI was not proven; historical route was ccy-based and lacked instId in response.
8. unit consistency result: current exact route exposes oi/oiCcy/oiUsd, but historical route exposes aggregate value/volume arrays; unit reconciliation is insufficient for exact-instrument research.
9. 4h alignment assessment: 1h historical ccy data can align to 4h only as aggregate context; current exact snapshots cannot support historical 4h validation.
10. gaps / duplicates / coverage issues: historical ccy-route row counts, modal intervals, gaps, and duplicates are documented per market; exact historical coverage remains the blocking issue.
11. usability decision: usable_only_as_aggregate_context; no exact-instrument OI strategy research should be defined from this data route alone.
12. recommended next direction: stay no-trade/benchmark-only unless a separate exact historical OI source is approved, or explicitly plan aggregate-context research with constraints.
13. what remains forbidden: strategy definition/testing, backtests, validation, threshold sweeps, source/parameter changes, dry-run/live planning, and reviving closed candidates.
14. implementation readiness judgment: closed / not ready.
15. commit / push result: pending at file creation time; verify final response for actual commit and push result.
16. next recommended Codex prompt: Create a research-only postmortem/synthesis for the exact OI audit result and decide whether to stop OI research or plan an aggregate-context-only feature audit.
17. one-sentence conclusion: Exact current OI exists, but historical exact-instrument OI was not proven through the audited public route, so OI remains aggregate-context only.
=== CHATGPT HANDOFF END ===
