# Short1 Failure-Mode Synthesis Update Round 1

## 1. Short1 Current Research State
Short1 structural discovery remains active only as research. The current evidence supports a path-quality parent, but it does not justify strategy implementation, thresholding, proxy changes, or live/dry-run strategy edits.

Current parent:

`below-EMA20 displacement mainly protects against adverse-dominant failure`

Leading antecedent:

`entry_short_ema20_gap_atr`

This antecedent is a diagnostic separator, not an implementation rule.

## 2. Material Base And Usable Markets
BTC alone was too sparse for Short1 discovery, so the active material base is the cross-market 4h basket.

Usable Short1 markets:

FILUSDT, DOTUSDT, ATOMUSDT, UNIUSDT, ADAUSDT, XRPUSDT, LTCUSDT, DOGEUSDT, NEARUSDT, ETCUSDT, AAVEUSDT

Executed Short1 total: 155

Starter short signal total: 474

## 3. Current Main Parent
The main parent remains:

`below-EMA20 displacement mainly protects against adverse-dominant failure`

Reason: adverse_dominant is the stable main failure target, and clean-vs-adverse_dominant separation is the strongest repeated structure across executed and starter populations.

## 4. Leading Antecedent
`entry_short_ema20_gap_atr` remains the leading antecedent candidate.

Clean-vs-adverse_dominant support:

- Executed: 10 / 11 markets
- Starter: 11 / 11 markets
- Both-population support: 10 / 11 markets
- Aggregate delta, executed clean minus adverse_dominant: 0.072787
- Aggregate delta, starter clean minus adverse_dominant: 0.064817

Boundary: this is not a threshold rule.

## 5. Stable Finding: Adverse-Dominant Failure Avoidance
Adverse_dominant is the stable primary failure target.

Counts:

- Executed adverse_dominant: 66
- Starter adverse_dominant: 227

Clean-vs-adverse_dominant displacement support:

- Executed: 10 / 11 markets
- Starter: 11 / 11 markets

Interpretation: below-EMA20 displacement appears most useful as protection against adverse-dominant failure, not as a universal clean-vs-all-failure separator.

## 6. Unresolved Behavior: Mixed_Chop
mixed_chop is separate unresolved behavior, not adverse_dominant-lite.

Counts:

- Executed mixed_chop: 16
- Starter mixed_chop: 29

Accepted interpretation: mixed_chop has much lower MAE and higher MFE-minus-MAE than adverse_dominant in both populations, so it is not just a softer adverse-dominant failure.

This bucket has meaningful favorable and adverse movement and should remain separate from adverse_dominant.

## 7. Unresolved Behavior: Weak_Followthrough
weak_followthrough is unresolved underpowered / transition followthrough.

Counts:

- Executed weak_followthrough: 11
- Starter weak_followthrough: 41

Accepted interpretation: weak_followthrough has favorable 24-bar short return by definition, but MFE is not dominant over MAE; aggregate path affinity is split (executed closer to mixed_chop, starter closer to adverse_dominant), and per-market evidence is sparse/inconsistent.

Affinity note: executed mixed_chop; starter adverse_dominant

This bucket has favorable return but poor excursion quality. It does not replace or expand the main parent.

## 8. Too-Small Behavior: Failed_No_Followthrough
failed_no_followthrough remains too small to interpret.

Counts:

- Executed failed_no_followthrough: 1
- Starter failed_no_followthrough: 1

No parent update should be made from this bucket.

## 9. Secondary Hints And Deprecated Directions
Lower `entry_adx` remains a secondary context hint only.

ADX clean-vs-adverse_dominant support:

- Executed: 10 / 11
- Starter: 8 / 11

Deprecated or deprioritized directions:

- Combined antecedents did not improve stability over displacement alone.
- `entry_exec_distance_atr` remains secondary and weaker upstream.
- DI fields and resumption fields remain weak or contradictory.
- Boolean repo-native flags are mostly not separative because starter construction already forces many to pass.

## 10. Closed / Forbidden Work
Forbidden from this state:

- Do not modify strategy/source files.
- Do not create implementation rules.
- Do not threshold `entry_short_ema20_gap_atr`.
- Do not threshold sweep.
- Do not change proxy definitions.
- Do not import Long1 structure.
- Do not assume Short1 is Long1 inverse.
- Do not promote mixed_chop or weak_followthrough into implementation layers.

## 11. Allowed Future Discovery Work
Allowed only as future descriptive research:

- A fixed unresolved non-clean grouping check comparing weak_followthrough and mixed_chop, if needed.
- A context-only ADX review, if kept secondary and descriptive.
- A synthesis/handoff note preserving boundaries before any additional diagnostics.

Any future work must keep executed Short1 and starter_short_signal populations separate.

## 12. Implementation Readiness Boundary
Short1 is not implementation-ready.

Current evidence supports a defensible discovery parent, but not a strategy rule, filter, threshold, or dry-run prototype.

## 13. Recommended Next Step
Pause implementation and create a concise handoff/scope note before any further Short1 diagnostics. If discovery continues later, the only justified next diagnostic is a fixed descriptive unresolved non-clean grouping check; no thresholding or implementation planning.
