# Short1 Discovery Synthesis Round 1

## 1. Short1 Research State

Short1 structural discovery is active through the cross-market 4h basket. This synthesis consolidates saved D: workspace outputs only and does not run a new diagnostic.

Current best Short1 parent wording:

`below-EMA20 displacement mainly protects against adverse-dominant failure`

This is a discovery parent, not an implementation layer. The parent says that the clearest currently observed Short1 structure is not generic shorting pressure and not a Long1 inverse. It is a path-quality distinction where clean downside followthrough is most clearly separated from adverse-dominant failure by sufficient below-EMA20 displacement.

## 2. Material Base

BTC alone was too sparse for Short1 discovery, so the usable material base moved to the cross-market 4h basket.

Cross-market material inventory:

- Total markets inspected: 19
- Usable markets: 11
- Borderline markets: 5
- Too-sparse markets: 3
- Aggregate executed Short1 trades: 184
- Aggregate starter short-signal opportunities: 540

Usable Short1 basket:

- FILUSDT
- DOTUSDT
- ATOMUSDT
- UNIUSDT
- ADAUSDT
- XRPUSDT
- LTCUSDT
- DOGEUSDT
- NEARUSDT
- ETCUSDT
- AAVEUSDT

The current accepted label base used by later audits is:

- Executed Short1 total: 155
- Starter short-signal total: 474

## 3. First Discovery Parent

The discovery parent evolved through the saved audits:

- Initial stable parent: `adverse-excursion-avoidant downside followthrough`
- Failure-mode refinement: `clean downside followthrough versus adverse-dominant failure`
- Current synthesis parent: `below-EMA20 displacement mainly protects against adverse-dominant failure`

Why this parent is defensible:

- Path-quality separation was stable across 11/11 usable markets.
- Adverse-dominant was the largest failure bucket in both executed and starter populations.
- Every usable market had adverse_dominant as the dominant failure mode in both executed Short1 and starter_short_signal.
- Below-EMA20 displacement was the strongest clean-vs-adverse_dominant pre-entry separator.

## 4. Leading Antecedent

Leading antecedent:

`entry_short_ema20_gap_atr`

Interpretation:

Below-EMA20 displacement appears to protect clean downside followthrough mainly by separating it from adverse-dominant failure.

Clean vs adverse_dominant support:

- Executed Short1: 10/11 markets
- Starter short-signal: 11/11 markets

Clean-vs-adverse aggregate displacement:

- Executed clean avg: 0.442422
- Executed adverse_dominant avg: 0.369635
- Executed delta: 0.072787
- Starter clean avg: 0.455403
- Starter adverse_dominant avg: 0.390586
- Starter delta: 0.064817

Aggregate predictor ranking:

- `entry_short_ema20_gap_atr`: executed 10/11, starter 11/11, both-population support 10/11
- Contradiction count: 1

## 5. What The Antecedent Explains

`entry_short_ema20_gap_atr` explains the strongest observed clean-vs-adverse_dominant separation.

Executed bucket profile:

- Clean followthrough count: 61, gap avg 0.442422
- Adverse_dominant count: 66, gap avg 0.369635

Starter bucket profile:

- Clean followthrough count: 176, gap avg 0.455403
- Adverse_dominant count: 227, gap avg 0.390586

The current read is: clean Short1 followthrough tends to appear after more sufficient below-EMA20 displacement than adverse-dominant failure.

## 6. What The Antecedent Does NOT Explain

`entry_short_ema20_gap_atr` does not cleanly separate clean followthrough from every non-clean outcome.

Clean vs weak_followthrough:

- Executed support: 1/6
- Starter support: 8/11

Clean vs mixed_chop:

- Executed support: 3/9
- Starter support: 4/9

Clean vs all_non_clean is stronger, but this is mostly driven by adverse_dominant dominance:

- Executed clean vs all_non_clean support: 10/11
- Starter clean vs all_non_clean support: 10/11

Therefore, below-EMA20 displacement is not a universal clean-vs-all-failure rule.

## 7. Secondary Context Hints

Secondary context:

`entry_adx`

Current read:

Lower ADX is broadly supportive but not uniquely adverse-dominant-specific.

- `entry_adx`: executed 10/11, starter 8/11, both-population support 8/11
- Executed clean ADX avg: 24.538 vs adverse_dominant 27.500
- Starter clean ADX avg: 24.412 vs adverse_dominant 26.763

Weaker or unstable hints:

- `entry_exec_distance_atr`: executed 9/11, starter 5/11; useful but weaker upstream
- DI fields: mixed and more contradictory
- Resumption fields: useful in places but not stable enough to promote
- Boolean repo-native flags mostly do not separate because starter-short construction already forces many of them to pass

## 8. Unresolved Buckets

Weak followthrough:

- Executed count: 11
- Starter count: 41
- Not cleanly explained by displacement; executed support is weak and many markets are sample-small.

Mixed chop:

- Executed count: 16
- Starter count: 29
- Not cleanly explained by displacement; mixed_chop often has comparable displacement to clean followthrough.

Failed no followthrough:

- Executed count: 1
- Starter count: 1
- n=1; do not interpret strongly.

## 9. Contradiction / Weak Areas

Key contradiction / weak areas:

- `LTCUSDT`: executed contradiction for `entry_short_ema20_gap_atr` in clean-vs-adverse_dominant.
- `AAVEUSDT`: executed clean sample is small in several comparisons.
- `NEARUSDT`: sample caution in executed adverse_dominant comparisons and prior starter contradiction in broader antecedent checks.
- Weak_followthrough and mixed_chop remain unresolved and should not be merged into adverse_dominant.
- Combined antecedents did not improve stability and should not be promoted.

## 10. Closed / Forbidden Work

Closed / forbidden for the current Short1 phase:

- Do not implement Short1 changes.
- Do not create or edit strategy rules.
- Do not threshold `entry_short_ema20_gap_atr`.
- Do not threshold-sweep any candidate field.
- Do not change proxy definitions.
- Do not merge weak_followthrough, failed_no_followthrough, or mixed_chop into adverse_dominant unless already labeled that way.
- Do not import Long1 structure into Short1.
- Do not assume Short1 is the inverse of Long1.
- Do not promote combined antecedents.
- Do not treat secondary hints as implementation filters.

## 11. Allowed Future Work

Allowed future discovery work:

- Create synthesis notes from saved outputs.
- Inspect adverse_dominant more deeply while keeping populations separate.
- Compare adverse_dominant vs mixed_chop descriptively.
- Investigate weak_followthrough separately.
- Study whether the displacement antecedent persists under fixed, non-swept descriptive groupings.
- Re-run descriptive audits only if source labels are missing or need reproducibility checks.

## 12. Implementation Readiness Boundary

Implementation readiness:

`not implementation-ready`

The current Short1 evidence is structural discovery evidence. It identifies a defensible parent and a leading antecedent, but it does not define a deployable rule, filter, threshold, or patch.
