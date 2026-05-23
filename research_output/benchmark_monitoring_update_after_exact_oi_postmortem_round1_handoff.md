=== CHATGPT HANDOFF START ===
1. run status: benchmark_monitoring_update_after_exact_oi_postmortem_round1 created as monitoring update only; no data fetch, strategy definition, validation, backtest, tuning, source change, dry-run, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before this update was db587c8 research: add exact OI audit postmortem.
3. commands run: verified branch/HEAD and required context files; inspected OI and funding postmortem decisions; created five monitoring update outputs; verified files; staged only benchmark_monitoring_update_after_exact_oi_postmortem_round1.* outputs; committed and pushed.
4. files changed / output paths: research_output/benchmark_monitoring_update_after_exact_oi_postmortem_round1_note.md; _status.csv; _allowed_forbidden.csv; _reopen_conditions.csv; _handoff.md.
5. current research status: OHLCV-only research failed, Candidate D is parked, funding feature failed, exact OI cannot advance from the current route, no active strategy is approved, and no-trade remains default.
6. exact OI interpretation: current exact OI snapshots are unit checks only; historical OI is aggregate/ccy-level context and not proven instrument-level history.
7. funding feature interpretation: funding-gated Candidate D reduced losses but did not create edge, so funding is observation-only unless a fresh approved plan exists.
8. benchmark-only monitoring scope: BTCUSDT 4h context, passive BTC benchmark, no-trade baseline, volatility regime, aggregate OI context only with non-instrument-level labeling, and funding context observation only.
9. what remains forbidden: trade signals, entries/exits, dry-run readiness, live readiness, implementation claims, threshold sweeps, Candidate D/funding tuning, exact OI strategy from current route, and bot restart.
10. reopen conditions: explicit approval plus genuinely new data source, external exact-OI vendor audit, strict aggregate-context-only audit plan, or fresh feature inventory.
11. GCP/bot recommendation: keep the bot stopped; infrastructure should not be restarted without a separately approved and validated strategy path.
12. implementation readiness judgment: closed / not ready.
13. commit / push result: pending at file creation time; verify final response for actual commit and push result.
14. next recommended Codex prompt: Create a benchmark-only monitoring note after exact OI audit closure, or create a plan-only aggregate-context OI audit with strict non-instrument-level constraints.
15. one-sentence conclusion: The project remains in no-trade benchmark-only observation mode after exact OI failed to provide usable historical instrument-level data.
=== CHATGPT HANDOFF END ===
