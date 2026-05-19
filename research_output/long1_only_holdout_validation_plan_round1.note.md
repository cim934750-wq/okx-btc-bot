# long1_only_holdout_validation_plan_round1

## 1. Validation Objective
Predeclare the validation design before seeing new results. The exact question is: Is Long1-only robust enough to remain the base research candidate after holdout/new-data validation?

This plan does not run validation, does not run a backtest, and does not change strategy behavior. It defines research gates only, not implementation gates.

## 2. Candidate Under Test
The candidate is frozen as final unit-fixed Long1-only:

- `allow_longs = True`
- `allow_shorts = False`
- `enable_add_on_entries = False`
- Long1 only
- no Long2
- no Short1
- no Short2
- no parameter changes
- no threshold changes
- final unit-fixed source only

## 3. Data Scope Options
Allowed validation data scopes:

A. Time-based holdout within existing 4h data: split each market chronologically, preferably 70% train/reference and 30% holdout, or pre-2023 vs post-2023 if all market date ranges support it. The holdout must not be used for tuning.

B. New-data extension: add later OHLCV candles after the current dataset end for the same symbols and same 4h timeframe. No parameter changes are allowed after seeing new data.

C. Market holdout: hold out a predeclared subset of symbols. The subset must include weak markets and major markets, not only prior winners. Market holdout is secondary because 19 markets is not a large universe.

## 4. Recommended Primary Validation Design
Primary design: time-based holdout across the same 19 local 4h markets, with a chronological split per market. Prefer 70% reference / 30% holdout if date coverage is sufficient.

Secondary design: new-data extension using later 4h OHLCV for the same 19 symbols if fresh data can be obtained cleanly and consistently.

Market holdout is useful only as a secondary robustness lens because the universe is small.

## 5. Predeclared Metrics
Compute net PnL, PF, max DD %, win rate, average trade, median trade, trade count, positive/negative market count, top 3 market PnL concentration %, top 5 market PnL concentration %, top 10 positive trade contribution %, BTCUSDT-specific metrics, majors-vs-all-market proxy metrics, and DOGE/DOT/UNI weak-market metrics.

## 6. Predeclared Pass / Caution / Fail Bands
Pass is research-only and requires all of the following: aggregate holdout net PnL > 0, PF >= 1.10, BTCUSDT net PnL >= 0 and PF >= 1.05, at least 10 of 19 markets positive, top 3 concentration <= 75%, top 5 concentration <= 100%, top 10 positive trade contribution <= 65%, and DOGE/DOT/UNI do not expand into a broader weak-market cluster.

Caution applies when aggregate is positive but one or more robustness dimensions are weak: PF 1.00 to <1.10, positive markets 8-9 of 19, BTC positive but basket weak, top 3 concentration >75%, top 5 >100%, or top 10 positive trade contribution >65%.

Fail applies if aggregate net PnL <= 0, PF < 1.00, BTCUSDT net PnL < 0, positive markets <=7 of 19, strong negative markets expand materially, top 3 concentration >=90%, or top 10 positive trade contribution >=80%.

These are research gates only. Passing them does not imply implementation readiness.

## 7. BTCUSDT Boundary
BTCUSDT support is useful but not sufficient alone. BTCUSDT failure is serious for this project. BTC-only success cannot override broad market concentration unless a separate BTC-only strategy decision is explicitly approved and validated.

## 8. Weak-market Treatment
DOGE, DOT, and UNI must stay visible in validation. They must not be removed after seeing holdout results. Track whether they remain weak. Any future exclusion/filter must be predeclared and separately validated. Do not cherry-pick them out in the same validation.

## 9. Concentration / Outlier Rules
Judge concentration with top 3 market contribution, top 5 market contribution, top 10 positive trade contribution, skew, and best-trade dependency if available. Positive aggregate is not enough if concentration worsens materially.

## 10. Required Outputs For Future Validation Run
Future validation should use prefix `long1_only_holdout_validation_round1` and produce market metrics, aggregate metrics, BTCUSDT relevance, market breadth, concentration risk, weak-market review, pass/fail decision, recommendation, and note outputs.

## 11. Allowed Future Work
Allowed only after this plan: execute the predeclared holdout validation, fetch/update new 4h OHLCV data if explicitly approved, run BTC-only vs basket comparison, run weak-market failure review after holdout, and run outlier sensitivity audit after holdout.

## 12. Forbidden Future Work
Forbidden: parameter optimization, threshold sweeping, choosing markets after seeing results, dropping DOGE/DOT/UNI without predeclared validation, live/dry-run planning from current evidence, implementation-readiness claim, merging research branch as production strategy, and claiming profitability from in-sample evidence.

## 13. Decision Tree After Validation
If pass: create a Long1-only candidate synthesis update, still make no implementation claim, and consider a separate dry-run readiness plan only after explicit approval.

If caution: run weak-market/outlier review, no dry-run.

If fail: park Long1-only as current candidate and do not continue toward implementation.

If mixed: define whether BTC-only research path is justified, without treating BTC alone as sufficient.

## 14. Implementation Readiness Boundary
Implementation readiness remains closed / not ready. This is a validation plan only. It does not authorize dry-run, live planning, production merge, or profitability claims.

## 15. Recommended Next Action
Pause and, if approved, execute only the predeclared holdout validation exactly as specified here.
