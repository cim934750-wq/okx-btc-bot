# External Exact-Data Audit Plan Round 1 Handoff

- Purpose: plan-only audit of external exact historical data sources for instrument-level trades, taker flow, OI, basis, funding, and premium/index context.
- Why next: CP1 public-trade reconstruction failed under cap; exact historical OI was not proven; aggregate taker flow is not exact instrument-level.
- Source families: OKX official/download/REST routes, ccxt/CCXT Pro wrappers, CryptoCompare, Kaiko, CoinAPI, Tardis.dev, Amberdata, Coin Metrics, Glassnode, Coinglass, The Tie, VeloData, Laevitas, AWS/GCP/BigQuery datasets, and local artifact references.
- Data contract: exact instrument ID, UTC timestamp, raw provenance, category-specific fields, clear taker-side/OI/basis semantics, license/cost notes, and 4h alignment support.
- Minimal sample audit proposal: BTC-USDT-SWAP first, DOGE-USDT-SWAP second only after BTC passes, one 4h bucket or one UTC day, raw archive and data dictionary required.
- Stop conditions: no exact OKX swap support, ambiguous taker side, non-instrument OI, shallow history, unclear/unacceptable cost/license, or unreproducible raw data.
- Default: no-trade / benchmark-only observation remains active; no implementation readiness.
