=== CHATGPT HANDOFF START ===
1. run status: oi_funding_data_availability_audit_plan_round1 completed as planning/audit-design only; no data fetch, backtest, validation, strategy definition, tuning, source change, dry-run/live, or implementation claim.
2. branch / workspace state: research/long1-only-candidate-robustness; based on b40c732.
3. commands run: verified branch/HEAD; inspected 19 local 4h markets, feature inventory, autonomous failure synthesis, Candidate D failure context, and local cache/path context; created/verified audit-plan outputs; staged/committed/pushed only new audit-plan files.
4. files changed / output paths: research_output/oi_funding_data_availability_audit_plan_round1_*.
5. audit objective: determine whether open-interest and funding-rate history are available, clean, unit-consistent, and alignable to prior 4h research windows before any strategy definition.
6. markets / instruments to check: same 19 spot-style markets mapped to candidate OKX USDT swap IDs like BTC-USDT-SWAP; BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT remain visible.
7. possible data sources: OKX native public API, ccxt OKX public methods, existing local cache if present, and third-party vendors only as future option.
8. required fields: timestamp, symbol/instrument, OI value/unit, funding rate, funding/next funding timestamps if available, source/provenance, raw archive/hash, future fetch timestamp.
9. alignment and coverage rules: 4h OHLCV alignment, UTC timestamps, no future leakage, no default forward-fill, explicit 8h funding handling, OI sampling-frequency documentation, gaps/duplicates/missing-market reporting.
10. usability criteria: usable, partially usable, or not usable based on market coverage, BTC/key-market visibility, history overlap, unit consistency, alignment feasibility, and missing-data severity.
11. future strategy classes unlocked: funding mean-reversion, OI expansion breakout, OI divergence filter, crowded-position avoidance, squeeze-risk filter, funding/OI regime classifier.
12. what remains forbidden: data fetch in this task, backtests/validation, strategy definition, tuning/sweeps, failed-candidate revival, dry-run/live, implementation claim.
13. implementation readiness judgment: closed / not ready.
14. commit / push result: pending at file creation time.
15. next recommended Codex prompt: Execute the OI/funding data availability audit for the same 19 markets, fetching only approved public historical OI/funding data and producing coverage/provenance outputs; do not define or test a strategy.
16. one-sentence conclusion: OI/funding research can reopen only after data availability and alignment are proven, not before.
=== CHATGPT HANDOFF END ===
