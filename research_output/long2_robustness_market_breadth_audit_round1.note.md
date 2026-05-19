# long2_robustness_market_breadth_audit_round1

## Scope
Research-only Long2 robustness / market-breadth audit using final unit-fixed source. No source files, strategy parameters, thresholds, PR branches, or live/dry-run planning were changed.

## Data
Used 19 local 4h markets: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. BTCUSDT_1h.csv present and intentionally excluded. No new markets were added.

## Primary comparison
Compared `long_only_long1_long2` against `long_only_long1_only` with only the approved long-only/add-on toggles.

## Market breadth
Long2 variant delta improved 11 markets and worsened 8 markets. Labels: strong_positive=7, weak_positive=3, neutral=1, weak_negative=5, strong_negative=3.

## Concentration
Total closed Long2-tag PnL was 2469.26. Top 3 Long2 markets (BNBUSDT; ETHUSDT; XRPUSDT) contributed 2347.94, or 95.09% of total Long2 PnL. Top 5 contributed 2773.44, or 112.32% of total Long2 PnL. Percentages can exceed 100% because losing markets offset aggregate Long2 PnL.

## BTCUSDT
BTCUSDT supports Long2 marginally: full-variant delta 76.90, Long2 count 52, and Long2 PnL 156.20.

## Distribution / downside
Long2 trade distribution is positive in mean but has low win rate and outlier sensitivity assessment `outlier_sensitive`. Markets where PnL improved while DD worsened materially: 4. Markets where PnL and DD both worsened: 8.

## Candidate decision
`long2_market_filter_research_only`. This is not implementation readiness. Long2 remains research-only and should not be promoted universally from this audit alone.
