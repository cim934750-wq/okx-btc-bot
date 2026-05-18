# Long2 Post Unit Fix Exit Synthesis Round 1

## 1. Current unit-fix state
The current validation state has both known runtime unit mismatches fixed: ATR-distance management/add-on distances and trend_fail EMA price-level comparison. No new unit mismatch was identified in the accepted exit instrumentation audit.

This synthesis uses existing saved outputs only and does not run a new diagnostic, backtest, optimization, or parameter sweep.

## 2. What was fixed
- ATR-distance runtime scaling: management TP/stop/trail/breakeven distances and Long2/Short2 add-on in_profit distances are converted with `_to_runtime_distance` before comparison against runtime prices.
- trend_fail EMA runtime scaling: unscaled `ema50` is converted with `_to_runtime_price_level` before comparison with runtime `Close`.
- Trend_fail disagreement counts moved from long `425 -> 0` and short `166 -> 0`.

## 3. What changed after fixes
Aggregate counts across original baseline -> post Option A -> post trend_fail patch:
- Total: `1056 -> 2696 -> 2730`
- Long1: `872 -> 1668 -> 1678`
- Long2: `0 -> 501 -> 528`
- Short1: `184 -> 527 -> 524`
- Short2: `0 -> 0 -> 0`

Lifecycle compression remains:
- Long1 average duration: `16.32 -> 7.23 -> 8.29` bars
- Short1 average duration: `109.66 -> 9.29 -> 8.51` bars

Long2 gate accessibility is confirmed after both unit fixes: raw `3958`, active `1153`, in_profit `1101`, all gates `464`, exported `528`.

## 4. Exit attribution result
Long1 aggregate top exits:
- TP1 partial close: `562`
- trailing stop proxy: `510`
- base stop proxy: `303`
- breakeven floor stop proxy: `241`
- trend_fail close: `62`

Short1 aggregate top exits:
- TP1 partial close: `157`
- trailing stop proxy: `139`
- base stop proxy: `101`
- TP2 close: `55`
- trend_fail close: `36`
- breakeven floor stop proxy: `36`

Interpretation: compression is mixed and led by TP1 partial closes plus stop/trailing/breakeven proxy exits. Stop/trailing/breakeven labels remain proxy labels because broker stop-fill reasons are not exported directly.

## 5. Short2 status
Short2 remains zero after both unit fixes. Current Short2 gate state: raw `39`, active `3`, in_profit `0`, all gates `0`, exported `0`.

This indicates sparse active short add-on material plus in_profit failure among active candidates.

## 6. What this proves
- The known ATR-distance runtime unit blocker was fixed.
- The known trend_fail EMA runtime unit mismatch was fixed.
- Long2 gates can open under unit-consistent runtime comparisons.
- Exit attribution now separates exact strategy close events from stop-fill proxies.
- Lifecycle compression remains material and mixed.

## 7. What this does NOT prove
- It does not prove profitability.
- It does not prove Long2 is a successful strategy component.
- It does not prove implementation readiness.
- It does not justify live or dry-run planning.
- It does not resolve performance interpretation.

## 8. Remaining risks
- Stop/trailing/breakeven outcomes are proxy-labeled because explicit broker stop-fill reasons are unavailable.
- Long2 overlap complicates Long1 lifecycle attribution: Long1 with Long2 overlap `792` out of `1678`.
- Short2 remains unresolved as a zero-output path.
- Post-fix performance has not been audited.
- Lifecycle changes must not be ignored when interpreting Long2.

## 9. Closed work
- ATR-distance unit fix validation.
- trend_fail EMA unit fix validation.
- Exit-instrumentation attribution round 1.
- Long2 gate accessibility confirmation.
- Long1/Short1 structural discovery reopening is out of scope.

## 10. Allowed future work
- Post-unit-fix performance audit only after explicit approval.
- Long2-specific lifecycle interaction audit if needed.
- Short2-specific gating audit if needed.
- Post-fix backtest comparison only as research, not live planning.
- Synthesis and handoff updates.

## 11. Forbidden future work
- Optimization.
- Threshold sweeps.
- Live/dry-run planning.
- Performance claims without approved post-fix performance audit.
- Converting Long2 nonzero tags directly into strategy confidence.
- Ignoring Long1/Short1 lifecycle changes.
- Reopening closed Long1/Short1 discovery rounds.

## 12. Implementation readiness boundary
Implementation readiness remains closed. The current state supports research validation only, not deployment planning.

## 13. Recommended next action
Pause and wait for user review. If the user explicitly approves more research, choose one narrow next task: post-unit-fix performance audit, Long2-specific lifecycle interaction audit, or Short2-specific gating audit.
