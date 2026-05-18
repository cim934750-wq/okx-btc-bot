# Long2 Runtime Gate Synthesis Scope Note Round1

## 1. Current Long2 State
Long2 remains research-only. The local 4h basket contains 19 markets. Repo-native add-long material is substantial (`add_long_signal = 3958`), but actual executed `Long2` trades remain `0`. This is therefore not a Long2 performance study.

## 2. Long2 Execution Path Status
The Long2 execution path exists in `research.strategy`; the prior material inventory found that the branch can be reached in post-management active-long context. The absence of Long2 trades is not currently explained by missing tag/export support, missing Long2 code, `len(self.trades) < 2`, or `add_on_gap_bars`.

## 3. Gate Funnel Summary
- Baseline actual trades across the inspected 4h markets: `Long1 = 872`, `Long2 = 0`, `Short1 = 184`.
- Raw `add_long_signal`: `3958`.
- Post-management active-long add candidates: `1378`.
- Raw add-long bars outside eligible post-management active-long context: `2580`.
- `len(self.trades) < 2` pass: `1378 / 1378`.
- `add_on_gap_bars` pass: `1378 / 1378`.
- Runtime `in_profit` pass: `0 / 1378`.
- All runtime Long2 gates pass: `0 / 1378`.
- Scale-consistent diagnostic pass: `1324 / 1378`.

## 4. Runtime in_profit Scale-Mismatch Finding
The accepted audit finding is that runtime `Close` and average entry appear to be FractionalBacktest-scaled (`runtime_price_scale_seen = 1e-08`), while ATR appears to remain in unscaled market-price units. The Long2 gate compares `Close > avg_entry + atr * add_on_profit_atr`; that mixes scaled prices with an unscaled ATR threshold and makes runtime `in_profit` effectively unreachable.

## 5. What This Does and Does Not Prove
This proves that the observed zero Long2 executions are best explained by a runtime gate/reference issue in the current research backtest path. It does not prove Long2 opportunities are profitable, unprofitable, high-quality, low-quality, or implementation-ready. The scale-consistent diagnostic pass count is evidence of a unit mismatch, not a trading rule.

## 6. Why This Is Not Implementation-Ready
No patch is justified from this synthesis alone. Before any source change is considered, a fixed read-only validation must identify exact scaling lines, confirm where ATR units diverge, check whether the same mismatch exists elsewhere, confirm intended `add_on_profit_atr` units, and build a minimal reproducible comparison of current versus scale-consistent inputs.

## 7. Forbidden Future Work
- Source patch or strategy edit without explicit user approval.
- Threshold sweep or optimization.
- Converting the scale-consistent diagnostic pass into a trading rule.
- Long2 performance claims from zero executed Long2 trades.
- Implementation planning.
- Reopening Long1 or Short1.

## 8. Allowed Future Work
- Fixed scale-reference validation audit.
- Unit-style read-only reproduction of `in_profit` inputs.
- Source-level patch proposal only after explicit user approval.
- Post-patch backtest only after patch approval.
- Synthesis or handoff updates.

## 9. Required Pre-Patch Validation Checklist
The checklist is saved separately as CSV. All items are required before any patch proposal; none authorize a patch by themselves.

## 10. Recommended Next Action
Run one fixed read-only scale-reference validation audit, or keep this as a Long2 runtime-gate scope note until the user explicitly opens that validation.
