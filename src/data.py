from __future__ import annotations

import pandas as pd

from src.exchange import OKXExchangeClient


OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def fetch_ohlcv_dataframe(
    exchange_client: OKXExchangeClient,
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    limit: int = 300,
) -> pd.DataFrame:
    rows = exchange_client.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(rows, columns=OHLCV_COLUMNS)
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    numeric_columns = ["open", "high", "low", "close", "volume"]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    return df


def fetch_btc_usdt_ohlcv(
    exchange_client: OKXExchangeClient, timeframe: str = "1h", limit: int = 300
) -> pd.DataFrame:
    return fetch_ohlcv_dataframe(exchange_client, "BTC/USDT", timeframe, limit)
