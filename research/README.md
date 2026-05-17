# BTC MTF Trend Pullback Research

CSV format:

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`

Timeframe:

- Base input data must be 4H OHLCV bars.

Main commands:

- Backtest: `python -m research.run_backtest --csv data/BTCUSDT_4h.csv`
- Optimize phase 1: `python -m research.optimize --csv data/BTCUSDT_4h.csv --phase phase1_entry_frequency --trials 50`
- Inspect results: `python -m research.inspect_results --study-name phase1_entry_frequency_btc4h --top 10`
