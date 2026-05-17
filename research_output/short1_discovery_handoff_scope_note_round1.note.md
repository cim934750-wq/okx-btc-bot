# Short1 Discovery Handoff / Scope Note Round 1

## 1. Current Short1 State
Short1 remains in structural discovery. It has a defensible failure-mode parent, but it is not a strategy rule, filter, threshold, or implementation layer.

Active workspace: `D:\Bot\0412_Bot_short1_research_workspace`

Evidence base: saved D-workspace research outputs only.

## 2. Main Parent
`below-EMA20 displacement mainly protects against adverse-dominant failure`

This parent is stable enough to carry forward as discovery language, not implementation language.

## 3. Leading Antecedent
`entry_short_ema20_gap_atr`

Status: leading diagnostic antecedent only. It must not be converted into a threshold rule or filter.

Clean-vs-adverse support:

- Executed: 10 / 11
- Starter: 11 / 11
- Aggregate delta, executed: 0.072787
- Aggregate delta, starter: 0.064817

## 4. Bucket Ledger
| Bucket | Executed | Starter | Status |
|---|---:|---:|---|
| clean_followthrough | 61 | 176 | reference positive path-quality bucket |
| adverse_dominant | 66 | 227 | stable main failure target |
| mixed_chop | 16 | 29 | unresolved separate behavior |
| weak_followthrough | 11 | 41 | unresolved underpowered / transition behavior |
| failed_no_followthrough | 1 | 1 | too small to interpret |

Executed total: 155

Starter total: 474

## 5. Stable Findings
- `adverse_dominant` is the stable main failure target.
- `entry_short_ema20_gap_atr` separates clean_followthrough from adverse_dominant more reliably than it separates clean from weak_followthrough or mixed_chop.
- Lower `entry_adx` remains secondary context only.

## 6. Unresolved Behaviors
- `mixed_chop`: separate unresolved behavior, not adverse_dominant-lite.
- `weak_followthrough`: underpowered / transition followthrough with favorable return but poor excursion quality.
- `failed_no_followthrough`: n=1 in both populations, too small to interpret.

## 7. Closed / Forbidden Work
- No implementation planning.
- No threshold sweep.
- No strategy/source edits.
- No proxy-definition changes.
- Do not convert `entry_short_ema20_gap_atr` into a rule/filter.
- Do not promote combined antecedents.
- Do not import Long1 structure.
- Do not assume Short1 is Long1 inverse.

## 8. Allowed Future Work
Allowed future work must remain descriptive and fixed-scope:

- Fixed descriptive unresolved non-clean grouping check.
- mixed_chop-specific descriptive review.
- weak_followthrough-specific descriptive review.
- Context-only ADX review if it remains secondary.
- Synthesis / handoff updates.

## 9. Implementation Boundary
Short1 is not implementation-ready. The current evidence may guide future discovery, but it does not justify changing strategy logic, adding filters, selecting thresholds, or creating a dry-run prototype.

## 10. Recommended Next Action
Pause implementation. If work continues, use only a tightly scoped descriptive unresolved non-clean grouping check; otherwise carry this handoff forward as the current Short1 boundary document.
