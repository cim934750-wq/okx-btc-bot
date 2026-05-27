# Manual External Data Docs/Pricing Review Plan Round 1 Handoff

- Purpose: prepare a structured manual docs/pricing review before any vendor API call, scrape, purchase, sample audit, or strategy research.
- Sources: OKX official/download/REST, Tardis.dev, Kaiko, CoinAPI, Amberdata, Coin Metrics, CryptoCompare, Glassnode, Coinglass, VeloData, Laevitas, The Tie, AWS/GCP/BigQuery public datasets, and sources already listed in the external exact-data audit plan.
- Workflow: human reviewer manually checks docs/pricing/data dictionaries/licensing and fills evidence rows; unknowns remain unknown.
- Scoring: exact OKX swap support, taker-side clarity, OI granularity, basis/funding support, history depth, data dictionary clarity, provenance, archive/license safety, cost clarity, sample accessibility, and 4h alignment.
- Go rule: only one or two sources marked likely_viable_for_sample_audit can justify a future minimal BTC-USDT-SWAP sample audit after explicit approval.
- Stop rule: no exact support, ambiguous semantics, aggregate-only data, unclear cost/license, no archive rights, or no reproducible raw data stops the source.
- Default: no-trade / benchmark-only monitoring remains active; no implementation readiness.
