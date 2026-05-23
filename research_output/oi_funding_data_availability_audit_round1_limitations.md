# OI/Funding Data Availability Audit Round 1 Limitations

- This audit fetched public OKX data only; no private/account/order/trade data was used.
- Historical OI via ccxt/OKX supports `1h` but not `4h`; 4h alignment would require predeclared downsampling.
- Historical OI appears base-currency aggregate in the ccxt/OKX history response, while current OI is exact instrument-level. This is a major constraint for strategy research.
- Funding updates at 8h cadence. It must not be silently forward-filled to missing 4h candles.
- Coverage is recent and does not provide a full replacement for the entire prior OHLCV reference history.
- This audit does not define, test, or recommend any trading strategy.
- No-trade / benchmark-only observation remains the default, and implementation readiness remains closed.
