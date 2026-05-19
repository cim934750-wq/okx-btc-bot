# Long-Only Long2 Component Comparison Round 1

## Scope

Research-only comparison using final unit-fixed source. No source files were modified, no parameters or thresholds were changed, and no PR #1/#2/#3 changes or merges were made.

## Data Coverage

Used the same 19 local 4h markets as `post_unit_fix_performance_audit_round1`: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT. `BTCUSDT_1h.csv` was excluded.

## Variants

- `long_short_current`: current unit-fixed reference, longs/shorts/add-ons enabled.
- `long_only_long1_long2`: long-only, Long1 and Long2 enabled.
- `long_only_long1_only`: long-only, add-ons disabled.
- `short_only_reference`: short-only reference only.

## Aggregate Comparison

- long_short_current: trades 2730, tags 1678/528/524/0, net PnL 5761.965447, PF 1.152403, DD 0.203976, win 56.556777
- long_only_long1_long2: trades 2206, tags 1678/528/0/0, net PnL 7333.509864, PF 1.232954, DD 0.139232, win 58.068903
- long_only_long1_only: trades 1671, tags 1671/0/0/0, net PnL 4327.766888, PF 1.162619, DD 0.125259, win 64.272890
- short_only_reference: trades 524, tags 0/0/524/0, net PnL -1566.464354, PF 0.752575, DD 0.100483, win 50.190840

## BTCUSDT Comparison

- long_short_current: trades 224, tags 171/52/1/0, net PnL 483.713227, PF 1.269544, DD 0.258008, win 58.035714
- long_only_long1_long2: trades 223, tags 171/52/0/0, net PnL 498.158474, PF 1.279794, DD 0.258008, win 58.295964
- long_only_long1_only: trades 169, tags 169/0/0/0, net PnL 421.262939, PF 1.271672, DD 0.215844, win 62.721893
- short_only_reference: trades 1, tags 0/0/1/0, net PnL -14.373672, PF 0.000000, DD 0.018520, win 0.000000

## Long2 Component

Variant 2 vs Variant 3 aggregate delta net PnL: 3005.742977. Delta PF: 0.070335. Delta max drawdown pct: 0.013973.

Long2 improves full-variant net PnL in 11 markets and worsens it in 8 markets. Positive-delta markets: ADAUSDT, BCHUSDT, BNBUSDT, BTCUSDT, ETCUSDT, ETHUSDT, FILUSDT, LTCUSDT, SOLUSDT, TRXUSDT, XRPUSDT. Negative-delta markets: AAVEUSDT, ATOMUSDT, AVAXUSDT, DOGEUSDT, DOTUSDT, LINKUSDT, NEARUSDT, UNIUSDT.

## Short Parking Validation

Long-only Long1+Long2 vs current aggregate delta net PnL: 1571.544418. Delta PF: 0.080552. Delta max drawdown pct: -0.064745. Validation label: short_parking_supported.

## Candidate Decision

Classification: `short_parking_supported_but_long2_inconclusive`

Reason: short parking improves aggregate result, and Long2 helps aggregate, but Long2 market breadth is mixed

Recommendation: Park shorts; treat Long2 as inconclusive and require narrower Long2 robustness review before promotion.

## Boundary

This is candidate triage only. No profitability claim, implementation-readiness claim, live/dry-run recommendation, optimization, or threshold sweep is made.
