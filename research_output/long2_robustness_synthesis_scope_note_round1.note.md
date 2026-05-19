# long2_robustness_synthesis_scope_note_round1

## 1. Current Long2 Status
Long2 remains research-active only as a market-filter / robustness candidate. It should not be universally enabled from the current evidence. Shorts remain parked for research focus, and Long1 remains the long-only base candidate.

## 2. What Long2 Shows Positively
Long2 had 528 closed trades and aggregate Long2-tag PnL of 2469.26. The Long1+Long2 variant improved aggregate net PnL versus Long1-only by 3005.74. The Long2 variant improved 11 markets and worsened 8. Strong positive market labels were observed in 7 markets.

## 3. What Weakens Long2
Breadth is mixed: closed Long2-tag PnL was positive in 10 markets and negative in 9. Long2 worsened both PnL and drawdown in 8 markets: AAVEUSDT, ATOMUSDT, AVAXUSDT, DOGEUSDT, DOTUSDT, LINKUSDT, NEARUSDT, UNIUSDT. Smaller/alts proxy Long2 PnL was -333.56, with 3 positive and 5 negative delta markets.

## 4. Concentration / Outlier Risk
Top 3 Long2 PnL markets were BNBUSDT, ETHUSDT, XRPUSDT, contributing 95.09% of total Long2 PnL. Top 5 markets were BNBUSDT, ETHUSDT, XRPUSDT, ADAUSDT, BTCUSDT, contributing 112.32% because losing markets offset gains. Top 10 positive trades contributed 83.85% of total Long2 PnL. Mean Long2 PnL was 4.68, median was -4.17, win rate was 41.10%, and skew was 4.09. This is outlier-sensitive evidence.

## 5. BTCUSDT Relevance
BTCUSDT is marginally supportive, not decisive. Long1-only net PnL was 421.26; Long1+Long2 net PnL was 498.16; delta was 76.90. BTCUSDT Long2 count was 52, Long2 PnL was 156.20, and Long2 win rate was 42.31%.

## 6. Market-Family Proxy Interpretation
The family grouping is a proxy only and does not use external liquidity data. Majors BTC/ETH/BNB/SOL had Long2 PnL 2016.01 and 4/4 positive delta markets. Large alts had Long2 PnL 786.81, with 4 positive and 3 negative delta markets. Smaller/alts had Long2 PnL -333.56, with 3 positive and 5 negative delta markets.

## 7. Drawdown / Downside Relevance
Long2 improved PnL but worsened drawdown materially in 4 markets: ADAUSDT, BCHUSDT, SOLUSDT, XRPUSDT. It worsened both PnL and drawdown in 8 markets: AAVEUSDT, ATOMUSDT, AVAXUSDT, DOGEUSDT, DOTUSDT, LINKUSDT, NEARUSDT, UNIUSDT. This downside evidence blocks universal promotion.

## 8. Candidate Decision
`long2_market_filter_research_only`. Long2 may remain a research-only market-filter idea, but not a universally active candidate.

## 9. What This Proves
This proves that Long2 can open under the unit-fixed source and can contribute positively in aggregate within this research sample. It also proves that the positive contribution is not evenly distributed.

## 10. What This Does NOT Prove
This does not prove profitability, implementation readiness, live/dry-run readiness, or that Long2 should be enabled universally. It does not prove that market-family proxy behavior will hold out of sample.

## 11. Allowed Future Long2 Work
Allowed future work: pre-declared market-filter validation only, outlier sensitivity audit, majors-only vs all-market comparison, BTC/ETH/BNB/SOL focused holdout check, Long1-only vs Long1+Long2 robustness check on genuinely new data, and paper/dry-run consideration only after separate explicit approval and after performance validation.

## 12. Forbidden Future Long2 Work
Forbidden future work: universal Long2 promotion, threshold sweep, optimization, cherry-picking only positive markets, live/dry-run planning from current evidence, claiming implementation readiness, ignoring concentration risk, hiding losing markets, and merging a research branch as a production strategy.

## 13. Validation Required Before Reconsidering Long2
Before reconsidering Long2, require a predeclared market-filter rule, outlier sensitivity review, majors-only vs all-market comparison, genuinely new or holdout data validation, drawdown relevance review, and explicit no-performance-claim boundary.

## 14. Implementation Readiness Boundary
Implementation readiness remains closed / not ready. This scope note is research-only and does not authorize source promotion, live planning, or production deployment.

## 15. Recommended Next Action
Pause new diagnostics and use this scope note as the boundary document for any future explicitly approved Long2 validation.
