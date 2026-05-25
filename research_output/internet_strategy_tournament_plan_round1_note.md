# Internet Strategy Tournament Plan Round 1

## Scope
This is a research-only plan for an internet-sourced crypto strategy tournament. It creates a structured way to collect public strategy ideas, classify them into families, reduce each family to one simple frozen representative candidate, and compare executable candidates under common gates in a later task.

No validation, backtest, market-data fetch, production source change, parameter change, dry-run restart, live plan, or implementation-readiness claim is made here.

## Why This Direction
The prior one-hypothesis-at-a-time path did not produce an implementation-ready candidate. OHLCV-only long-only variants failed, Candidate D failed later data, the funding-gated variant failed, exact historical instrument-level OI was not proven, autonomous OHLCV discovery promoted zero candidates, and aggregate taker-flow gating produced zero trades. The next useful step is not another narrow retest; it is a controlled tournament plan with external idea diversity and strict anti-overfit controls.

## Collection Method
Public references may be collected from academic papers, arXiv/SSRN, Quantpedia-style summaries, Freqtrade and Jesse examples, TradingView public scripts as idea references only, exchange/data-provider educational pages, and reputable quant/trading blogs. Claimed online performance is never evidence. Paid/proprietary strategies, unverifiable screenshots, and code-copying are excluded.

## Normalization Method
Each reference is mapped to a strategy family. Each family gets at most one simple frozen representative candidate in the first pass. Rules must define entry, exit, stop, sizing, market scope, data source, and timing assumptions before validation. If data is unavailable or not audited, the family is plan-only or excluded until a data audit is explicitly approved.

## Tournament Method
Future validation should use the same 19 markets whenever feasible, with BTCUSDT, DOGEUSDT, DOTUSDT, and UNIUSDT visible in reporting. Every candidate must be compared against no-trade, passive BTC, per-market buy-and-hold where feasible, and previous failed candidates as references only. No-trade remains the default unless a candidate clears all predeclared gates and then survives a separate confirmation plan.
