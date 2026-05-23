# Exact-Instrument OI Audit Round 1 Limitations

- The audit fetched only public OI data and did not fetch OHLCV, private account data, order data, trade data, or funding data.
- The native current OKX endpoint provided exact instrument OI snapshots, but not historical exact-instrument series.
- The historical OKX Rubik route required `ccy` and returned array rows without `instId`; adding `instId` did not prove exact instrument filtering.
- The 1h historical route can only be treated as aggregate or currency-level context from this audit.
- Current exact OI cannot be used for historical validation by itself.
- Unit reconciliation between current exact fields and historical aggregate fields was not accepted as proof of exact instrument history.
- No forward-fill, inferred OI, synthetic values, or strategy rules were created.
- No implementation readiness, dry-run readiness, or live readiness is implied.
