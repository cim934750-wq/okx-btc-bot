=== CHATGPT HANDOFF START ===
1. run status: exact_instrument_oi_audit_postmortem_round1 created as research-only synthesis; no OI fetch, strategy definition, validation, backtest, tuning, source change, dry-run, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before this postmortem was 82024a3 research: add exact instrument OI availability audit.
3. commands run: verified branch/HEAD and audit inputs; inspected usability, coverage, alignment, and key-market unit rows; created seven postmortem outputs; verified files; staged only exact_instrument_oi_audit_postmortem_round1.* outputs; committed and pushed.
4. files changed / output paths: research_output/exact_instrument_oi_audit_postmortem_round1_note.md; _findings.csv; _exact_vs_aggregate.csv; _decision.csv; _allowed_next_steps.csv; _closed_items.csv; _handoff.md.
5. exact OI audit finding summary: current exact OI exists for 19/19 markets, but historical exact-instrument OI was not proven; historical route is ccy-level aggregate context.
6. exact current vs historical aggregate interpretation: current exact snapshots are unit checks only; historical ccy-level series can align to 4h only as aggregate context; exact historical instrument feature is unavailable from this route.
7. usability decision: usable_only_as_aggregate_context.
8. OI research decision: conservative default is stop_oi_research_keep_benchmark_only; aggregate-context-only audit or external vendor exact-OI audit remain optional with explicit approval.
9. what is now closed: exact-instrument OI strategy from current OKX/ccxt route, OI entry/exit strategy definition from current data, treating ccy OI as exact OI, dry-run/live planning, implementation readiness.
10. what remains allowed: no-trade default, benchmark-only monitoring, aggregate-context-only audit plan with strict constraints, external vendor exact-OI audit if approved, fresh feature inventory if genuinely new data appears.
11. recommended next direction: stop OI strategy research by default and keep benchmark/no-trade; optional next work is plan-only aggregate-context audit or vendor exact-OI availability audit.
12. what remains forbidden: OI strategy validation, backtests, threshold sweeps, aggregate-as-exact claims, source/parameter changes, dry-run/live plans, and reviving closed candidates.
13. implementation readiness judgment: closed / not ready.
14. commit / push result: pending at file creation time; verify final response for actual commit and push result.
15. next recommended Codex prompt: Create a benchmark-only monitoring update after exact OI audit postmortem, or create a plan-only aggregate-context OI audit with strict non-instrument-level constraints.
16. one-sentence conclusion: Exact OI research cannot advance from the current OKX/ccxt historical route because the usable history is aggregate context, not proven instrument-level data.
=== CHATGPT HANDOFF END ===
