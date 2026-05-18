# Post Unit Fix Performance Audit Round 1

## Scope

This is a research-only post-fix performance audit for the unit-fixed `research/strategy.py` source. It does not modify source files, strategy parameters, thresholds, PR #1, PR #2, or PR #3. It does not run optimization, threshold sweeps, live/dry-run planning, or implementation planning.

## Data Coverage

- Used 19 local 4h OHLCV files: AAVEUSDT, ADAUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, NEARUSDT, SOLUSDT, TRXUSDT, UNIUSDT, XRPUSDT.
- Excluded CSVs: BTCUSDT_1h.csv.
- BTCUSDT is reported separately in `market_metrics.csv` and included in the all-market 4h basket.

## Aggregate Current Unit-Fixed Result

- Total trades: 2730
- Long1 / Long2 / Short1 / Short2: 1678 / 528 / 524 / 0
- Net profit: 5761.965447
- Profit factor: 1.152403
- Max drawdown pct: 0.203976
- Win rate pct: 56.556777
- Avg trade: 2.110610
- Avg duration bars: 8.083516

## BTCUSDT Current Unit-Fixed Result

- Total trades: 224
- Long1 / Long2 / Short1 / Short2: 171 / 52 / 1 / 0
- Net profit: 483.713227
- Initial equity: 100000.000000
- Profit factor: 1.269544
- Max drawdown pct: 0.258008
- Win rate pct: 58.035714

## Tag-Level Interpretation

See `tag_metrics.csv` for counts, winners/losers, PnL, win rate, and PnL contribution by tag. Drawdown attribution is not directly inferable from closed trade rows, so worst-trade PnL is provided as a proxy only.

## Long2 Contribution

- Aggregate Long2 count: 528
- Aggregate Long2 total PnL: 2469.587118
- Aggregate Long2 avg trade: 4.677248
- Aggregate Long2 win rate pct: 41.098485
- Positive Long2 markets: ADAUSDT, BNBUSDT, BTCUSDT, ETHUSDT, FILUSDT, LINKUSDT, LTCUSDT, SOLUSDT, TRXUSDT, XRPUSDT
- Negative Long2 markets: AAVEUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, DOGEUSDT, DOTUSDT, ETCUSDT, NEARUSDT, UNIUSDT

This is descriptive candidate triage only and does not prove Long2 readiness.

## Short-Side Assessment

- Aggregate short-side total PnL: -1571.336998
- Short1 total PnL: -1571.336998
- Short2 count: 0
- Short-help markets: AVAXUSDT, DOTUSDT, ETHUSDT, NEARUSDT, TRXUSDT, XRPUSDT
- Short-drag markets: AAVEUSDT, ADAUSDT, ATOMUSDT, BCHUSDT, BTCUSDT, DOGEUSDT, ETCUSDT, FILUSDT, LINKUSDT, LTCUSDT, SOLUSDT, UNIUSDT

No short-side disabling or implementation change is proposed here.

## Three-State Comparison Boundary

A/B state counts are reused from prior compact summaries where recoverable. PnL/performance for A and B was not recoverable from compact retained summaries in this branch, so current final unit-fixed C performance is the primary measured state.

## Candidate Decision

Classification: `park shorts`

Reason: short side aggregate contribution is negative in the post-fix audit

## Boundary

No profitability claim, implementation-readiness claim, or live/dry-run recommendation is made.
