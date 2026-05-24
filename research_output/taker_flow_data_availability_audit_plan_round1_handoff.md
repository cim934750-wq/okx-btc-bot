=== CHATGPT HANDOFF START ===
1. run status: taker_flow_data_availability_audit_plan_round1 created as audit-plan only; no data fetch, strategy definition, validation, backtest, tuning, source change, dry-run, or live planning was performed.
2. branch / workspace state: research/long1-only-candidate-robustness in /Users/immuhyun/Documents/Coin_Demo/okx-btc-bot; source HEAD before this plan was c9736af research: add taker-flow feature research plan.
3. commands run: verified branch/HEAD and no leftover taker-flow process; inspected taker-flow research plan and prior monitoring/OI/funding/autonomous context; created eleven audit-plan outputs; verified files; staged only taker_flow_data_availability_audit_plan_round1.* outputs; committed and pushed.
4. files changed / output paths: research_output/taker_flow_data_availability_audit_plan_round1_note.md; _market_mapping.csv; _data_sources.csv; _required_fields.csv; _feature_formulas.csv; _alignment_rules.csv; _coverage_requirements.csv; _usability_criteria.csv; _future_strategy_classes.csv; _allowed_forbidden.csv; _handoff.md.
5. audit objective: determine whether historical taker buy/sell volume or taker-volume imbalance can be obtained for the same 19 markets and aligned to 4h research candles without leakage.
6. markets / instruments to check: same 19 spot-style symbols mapped to OKX USDT swaps, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT explicitly visible.
7. possible data sources: OKX native public REST, OKX Rubik/trading-data endpoints, ccxt public methods, existing local cache, public trade reconstruction, and third-party vendors only as future optional source.
8. required fields: timestamp, symbol/instrument, taker buy volume, taker sell volume or safe derivation, total volume, quote volume if available, ratio if only ratio exists, units, endpoint/method, provenance, future fetch timestamp, raw archive/hash, sampling interval, gaps, and duplicates.
9. feature formulas: taker_buy_ratio, taker_sell_ratio, taker_imbalance, taker_delta, abnormal_turnover, and range_volume_impulse are audit-only computability targets, not strategy rules.
10. alignment and coverage rules: align to closed 4h candles, no future leakage, no arbitrary forward-fill, aggregate lower-timeframe data into closed 4h buckets, classify sparse/higher-timeframe sources as unsuitable for 4h strategy features, and report coverage/gaps/duplicates/timezone.
11. usability criteria: usable_direct_taker_flow, usable_derived_from_public_trades, usable_ratio_only_context, partially_usable_short_history, or not_usable_for_research.
12. future strategy classes unlocked: taker-flow confirmed breakout, sell-imbalance exhaustion reversal, aggressive buy continuation, liquidation-wick bounce with flow confirmation, and low-flow chop no-trade filter, only after usable audit results and a separate frozen plan.
13. what remains forbidden: data fetch in this task, immediate strategy validation, threshold sweep, OHLCV-only retest, Candidate D/K/funding/OI path revival, dry-run/live planning, and implementation claims.
14. implementation readiness judgment: closed / not ready.
15. commit / push result: pending at file creation time; verify final response for actual commit and push result.
16. next recommended Codex prompt: Execute the taker-flow data availability audit for the same 19 markets, fetching only explicitly approved public taker buy/sell or taker-volume data and producing coverage/provenance outputs; do not define or test a strategy.
17. one-sentence conclusion: The next step is a guarded data audit for aggressive taker-flow features, not a strategy test.
=== CHATGPT HANDOFF END ===
