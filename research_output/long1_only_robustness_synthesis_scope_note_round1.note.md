# long1_only_robustness_synthesis_scope_note_round1

## 1. Current Long1-only Status
Long1-only is the cleanest base candidate so far, but it is still research-only and concentrated. Shorts remain parked for research focus. Long2 remains market-filter research only. No dry-run discussion is allowed before holdout/new-data validation.

## 2. Evidence Supporting Long1-only
Long1-only produced 1671 trades, net PnL 4327.77, PF 1.1626, max DD 0.1253%, win rate 64.27%, avg trade 2.59, and median trade 4.55. It was positive in 12 markets and negative in 7.

## 3. Evidence Weakening Long1-only
The result remains concentrated and has weak markets. Strong negative markets were DOGEUSDT, DOTUSDT, UNIUSDT. Weak negative markets were BCHUSDT, ETCUSDT, NEARUSDT, TRXUSDT. The worst 3 markets were DOTUSDT, UNIUSDT, DOGEUSDT, totaling -1613.60.

## 4. Concentration / Outlier Risk
Top 3 markets by Long1-only PnL were BNBUSDT, LTCUSDT, ETHUSDT, contributing 79.54% of total PnL. Top 5 were BNBUSDT, LTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, contributing 105.29% because losing markets offset gains. Top 10 positive trades contributed 68.44% of total PnL. Distribution assessment: outlier_sensitive.

## 5. BTCUSDT Relevance
BTCUSDT supports Long1-only as research evidence, not as sufficient validation. BTCUSDT had 169 trades, net PnL 421.26, PF 1.2717, max DD 0.2158%, win rate 62.72%, avg trade 2.49, and median trade 3.69.

## 6. Market-family Proxy Interpretation
The market-family grouping is only a proxy and uses no external liquidity data. Majors BTC/ETH/BNB/SOL had net PnL 3675.76, PF 1.5671, positive 4/4. Large alts had net PnL 290.63, PF 1.0277, positive 4/7. Smaller/alts had net PnL 361.37, PF 1.0376, positive 4/8.

## 7. Comparison Against Long1+Long2
Compared with Long1+Long2, Long1-only had PnL delta -3005.74, PF delta -0.0703, DD delta -0.0140pp, win-rate delta 6.20pp, and -535 fewer trades. It is simpler and lower-DD, but lower aggregate PnL/PF.

## 8. Comparison Against All-side Current
Compared with all-side current, Long1-only had PnL delta -1434.20, PF delta 0.0102, DD delta -0.0787pp, win-rate delta 7.72pp, and -1059 fewer trades. Short parking remains supported, but Long1-only gives up the positive aggregate Long2 contribution.

## 9. Candidate Decision
`long1_only_positive_but_concentrated`. This decision is frozen as research-only and does not authorize implementation.

## 10. What This Proves
This proves Long1-only is positive in the current 19-market research sample, simpler than Long1+Long2/all-side variants, and supported by BTCUSDT and the majors proxy group.

## 11. What This Does NOT Prove
This does not prove implementation readiness, production readiness, live/dry-run readiness, or that Long1-only is robust outside the current sample. BTCUSDT alone is not sufficient. Concentration risk remains material.

## 12. Allowed Future Long1-only Work
Allowed future work: predeclared holdout validation, genuinely new data validation, BTC-only vs 19-market basket comparison, majors-only vs all-market comparison, outlier sensitivity audit, weak-market failure review for DOGE/DOT/UNI, post-fix performance comparison only as research, and dry-run discussion only after separate explicit approval and after holdout validation.

## 13. Forbidden Future Long1-only Work
Forbidden future work: implementation promotion from current evidence, live/dry-run planning now, threshold sweep, optimization, cherry-picking only positive markets, hiding losing markets, claiming production readiness, merging research branches as strategy deployment, ignoring concentration risk, and treating BTCUSDT alone as sufficient.

## 14. Required Holdout/New-data Validation
Before any dry-run discussion, require a predeclared holdout plan, genuinely new data check, concentration sensitivity review, outlier sensitivity review, weak-market failure review, BTC-vs-basket boundary check, and explicit no-readiness-claim boundary.

## 15. Implementation Readiness Boundary
Implementation readiness remains closed / not ready. This synthesis is research-only and does not authorize source promotion, live planning, dry-run planning, or production deployment.

## 16. Recommended Next Action
Pause and use this synthesis as the boundary for any future explicitly approved Long1-only holdout/new-data validation.
