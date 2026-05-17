# Short1 Discovery Stop Marker Round 1

## 1. Current Short1 Parent
`below-EMA20 displacement mainly protects against adverse-dominant failure`

This is the final carry-forward discovery parent for the current Short1 first discovery round. It is not an implementation rule.

## 2. Leading Diagnostic Antecedent
`entry_short_ema20_gap_atr`

Status: diagnostic antecedent only. Do not convert it into a threshold, rule, or filter.

## 3. Bucket Ledger
| Bucket | Executed | Starter | Status |
|---|---:|---:|---|
| clean_followthrough | 61 | 176 | reference positive path-quality bucket |
| adverse_dominant | 66 | 227 | stable main failure target |
| mixed_chop | 16 | 29 | unresolved component behavior |
| weak_followthrough | 11 | 41 | unresolved underpowered / transition behavior |
| unresolved_non_clean | 27 | 70 | high-level ledger label only |
| failed_no_followthrough | 1 excluded | 1 excluded | too small to interpret |

## 4. Stable Findings
- `adverse_dominant` is the stable main failure target.
- Below-EMA20 displacement mainly protects against adverse-dominant failure.
- `entry_short_ema20_gap_atr` remains the leading diagnostic antecedent.

## 5. Unresolved Ledger
`mixed_chop` and `weak_followthrough` may be grouped descriptively as `unresolved_non_clean` for high-level ledger use only.

They must not be merged for detailed analysis because their path behavior differs.

Grouping reason:

mixed_chop and weak_followthrough can be grouped as unresolved_non_clean for a high-level ledger, but component behavior remains different: mixed_chop has non-favorable return with better MFE-MAE, while weak_followthrough has favorable return but adverse-dominant excursion quality. Keep component labels in analysis.

## 6. Closed Diagnostics
The following diagnostics are closed for the current Short1 first discovery round:

- Short1 material inventory
- FIL-first structural discovery
- path-quality stability audit
- followthrough antecedent audit
- below-EMA20 displacement audit
- combined antecedent audit
- path-quality failure-mode audit
- adverse-dominant predictor audit
- displacement cross-bucket audit
- adverse vs mixed_chop audit
- weak_followthrough audit
- unresolved non-clean grouping check

## 7. Forbidden Future Work
- Implementation planning.
- Threshold sweep.
- Source/strategy edits.
- Proxy-definition changes.
- Converting `entry_short_ema20_gap_atr` into a rule/filter.
- Promoting `mixed_chop` or `weak_followthrough` into final layers.
- Merging `mixed_chop` and `weak_followthrough` for detailed analysis.
- Importing Long1 structure.
- Assuming Short1 is Long1 inverse.

## 8. Allowed Future Work Only If Justified
- A genuinely new fixed descriptive question that is not a replay of completed diagnostics.
- Synthesis / handoff updates.
- Broader external validation material only if explicitly justified.
- No implementation.

## 9. Implementation Readiness Boundary
Short1 is not implementation-ready.

No strategy rule, filter, threshold, dry-run prototype, or source edit is justified by the current discovery round.

## 10. Final Carry-Forward Judgment
Stop the current Short1 first discovery round here. Carry forward the parent, leading diagnostic antecedent, bucket ledger, closed diagnostics list, and no-implementation boundary.
