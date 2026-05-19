# long1_only_candidate_robustness_audit_round1

## Scope
Research-only Long1-only robustness audit using final unit-fixed source. Config toggles only: allow_longs=True, allow_shorts=False, enable_add_on_entries=False. No source files, strategy parameters, thresholds, PR branches, or live/dry-run planning were changed.

## Data
Used 19 local 4h markets: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. BTCUSDT_1h.csv present and intentionally excluded. BTCUSDT_1h.csv was excluded from the audit.

## Aggregate Long1-only Result
Long1-only produced 1671 trades, net PnL 4327.77, profit factor 1.1626, max drawdown 0.1253%, and win rate 64.27%.

## Market Breadth
Positive markets: 12; negative markets: 7. Labels: strong_positive=8, weak_positive=4, neutral=0, weak_negative=4, strong_negative=3.

## Concentration
Top 3 Long1-only markets (BNBUSDT; LTCUSDT; ETHUSDT) contributed 3442.21, or 79.54% of aggregate PnL. Top 5 contributed 4556.54, or 105.29%. Worst 3 markets were DOTUSDT; UNIUSDT; DOGEUSDT.

## BTCUSDT
BTCUSDT had 169 trades, net PnL 421.26, PF 1.2717, max DD 0.2158%, and win rate 62.72%.

## Distribution
Mean PnL was 2.59, median PnL was 4.55, p25/p75 were -27.85/25.43, worst/best trade were -272.33/462.55, and skew was 1.58. Outlier assessment: outlier_sensitive.

## Comparison Judgment
Compared with Long1+Long2, Long1-only is simpler and had lower drawdown, but lower aggregate PnL and PF. Compared with all-side current, Long1-only removes short and add-on complexity and lowers drawdown, but aggregate PnL is lower because Long2 was positive in aggregate.

## Candidate Decision
`long1_only_positive_but_concentrated`. This is research-only candidate triage and does not imply implementation readiness.
