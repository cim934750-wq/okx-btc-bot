=== CHATGPT HANDOFF START ===
1. run status: oi_funding_data_availability_audit_round1 completed as research-only public data availability audit; no strategy definition, backtest, validation, tuning, production change, dry-run/live, or implementation claim.
2. branch / workspace state: research/long1-only-candidate-robustness; based on aaa892e.
3. commands run: verified branch/HEAD and 19 markets; loaded audit plan; fetched OKX public funding history, OI history, and current OI via ccxt; wrote raw/audit outputs; verified files; staged/committed/pushed only audit artifacts.
4. files changed / output paths: research_output/oi_funding_data_availability_audit_round1_* and research_output/oi_funding_data_availability_audit_round1_raw/.
5. markets / instruments audited: 19 markets mapped to OKX swap IDs such as BTC-USDT-SWAP; BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remained visible.
6. data sources / endpoints used: OKX public via ccxt 4.2.14: fetchFundingRateHistory, fetchOpenInterestHistory(1h), fetchOpenInterest current.
7. open interest availability summary: historical OI fetched for 19/19 markets but is constrained as 1h/base-currency aggregate history; current exact instrument OI fetched for unit checks.
8. funding-rate availability summary: funding history fetched for 19/19 markets with 8h cadence and broad key-market coverage.
9. alignment assessment: funding aligns sparsely to every second 4h candle; OI can be downsampled from 1h to 4h but carries instrument-specific history limitations; no forward-fill by default.
10. gaps / duplicates / unit issues: see gaps_duplicates; main unit issue is historical OI not exact inst-specific via this route, while funding is decimal per funding interval.
11. usability decision: partially_usable_needs_constraints; funding is usable with sparse-alignment constraints, OI is partially usable and needs constraints or deeper exact-instrument audit.
12. recommended next direction: create a funding-first or constrained funding/OI frozen-definition plan only after explicit approval, or run deeper native REST/vendor audit for exact historical OI.
13. what remains forbidden: strategy definition, backtests/validation, parameter tuning/sweeps, failed-candidate revival, dry-run/live, implementation claim.
14. implementation readiness judgment: closed / not ready.
15. commit / push result: pending at file creation time.
16. next recommended Codex prompt: Create a research-only frozen-definition plan for a funding-rate feature candidate using the audited data constraints; do not run validation yet.
17. one-sentence conclusion: Funding data is broadly available, but OI history is constrained, so strategy research can only proceed with explicit frozen constraints and no implementation claim.
=== CHATGPT HANDOFF END ===
