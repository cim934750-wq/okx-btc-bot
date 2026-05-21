# Candidate D Later-Data Fetch Validation Round 1 Limitations

- Later-data window is short for most non-BTC markets because many existing local files already ended near 2026-05-16.
- OKX returned fetched candles starting one 4h interval after the requested start for each market; this initial source gap is documented in data coverage and was not filled.
- BTCUSDT local history ended earlier than most markets, so BTCUSDT later coverage is longer than the rest of the basket.
- Indicators used prior local history only as warmup; trades were evaluated only on fetched later candles.
- Fetched data source is okx_public_ohlcv_via_ccxt; results may differ from other venues.
- OHLC ambiguity remains handled conservatively: stop first, then the lower positive exit if EMA20 and take-profit are both possible.
- Extra slippage/fee sensitivity is approximate and research-only.
- This validation does not authorize dry-run, live trading, production implementation, or parameter changes.
- Implementation readiness remains closed / not ready.
