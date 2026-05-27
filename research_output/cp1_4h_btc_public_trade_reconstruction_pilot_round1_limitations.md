# CP1 4h BTC Public-Trade Reconstruction Pilot Limitations

- CP1 covers exactly one completed UTC 4h interval for BTC-USDT-SWAP only.
- CP1 does not prove 1-day, 7-day, 30-day, DOGE, DOT, or all-19 feasibility.
- CP1 does not validate any trading strategy or active edge.
- Side semantics are accepted from previously committed local audit evidence, not from independent order-book replay.
- Volume fields use OKX trade `sz` units; notional reconstruction and contract metadata were not audited in CP1.
- Any incomplete bucket, unresolved pagination risk, duplicate conflict, side-semantics uncertainty, or resource-budget breach blocks CP2 advancement.
