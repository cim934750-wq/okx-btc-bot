from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Optional

import ccxt

from src.config import BotConfig


logger = logging.getLogger(__name__)


class OKXExchangeClient:
    def __init__(self, config: BotConfig):
        self.config = config
        exchange_config: dict[str, Any] = {
            "enableRateLimit": True,
            "options": {
                "defaultType": config.okx_default_type,
            },
        }

        if config.api_keys_available:
            exchange_config.update(
                {
                    "apiKey": config.okx_api_key,
                    "secret": config.okx_secret_key,
                    "password": config.okx_passphrase,
                }
            )
        else:
            logger.warning(
                "OKX API credentials are missing; private account functions are disabled. "
                "Market-data-only dry-run mode is allowed."
            )

        self.exchange = ccxt.okx(exchange_config)

        if config.okx_demo:
            logger.info("OKX demo trading header will be applied to private calls")

    @contextmanager
    def _private_headers(self):
        original_headers = dict(getattr(self.exchange, "headers", {}) or {})
        if self.config.okx_demo:
            self.exchange.headers = {
                **original_headers,
                "x-simulated-trading": "1",
            }
        try:
            yield
        finally:
            self.exchange.headers = original_headers

    def fetch_balance(self) -> dict[str, Any]:
        if not self.config.api_keys_available:
            logger.warning("Skipping fetch_balance: private OKX credentials are not configured")
            return {}
        with self._private_headers():
            return self.exchange.fetch_balance()

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[list[Any]]:
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if self.config.dry_run:
            raise RuntimeError("Cannot create order: DRY_RUN=1")
        if not self.config.api_keys_available:
            raise RuntimeError("Cannot create order: private OKX credentials are not configured")
        with self._private_headers():
            return self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params or {},
            )

    def cancel_order(
        self,
        order_id: str,
        symbol: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if self.config.dry_run:
            raise RuntimeError("Cannot cancel order: DRY_RUN=1")
        if not self.config.api_keys_available:
            raise RuntimeError("Cannot cancel order: private OKX credentials are not configured")
        with self._private_headers():
            return self.exchange.cancel_order(order_id, symbol=symbol, params=params or {})

    def fetch_open_orders(self, symbol: Optional[str] = None) -> list[dict[str, Any]]:
        if not self.config.api_keys_available:
            logger.warning("Skipping fetch_open_orders: private OKX credentials are not configured")
            return []
        with self._private_headers():
            return self.exchange.fetch_open_orders(symbol=symbol)


def fetch_balance(client: OKXExchangeClient) -> dict[str, Any]:
    return client.fetch_balance()


def fetch_ohlcv(
    client: OKXExchangeClient, symbol: str, timeframe: str, limit: int
) -> list[list[Any]]:
    return client.fetch_ohlcv(symbol, timeframe, limit)


def create_order(
    client: OKXExchangeClient,
    symbol: str,
    order_type: str,
    side: str,
    amount: float,
    price: Optional[float] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return client.create_order(symbol, order_type, side, amount, price, params)


def cancel_order(
    client: OKXExchangeClient,
    order_id: str,
    symbol: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return client.cancel_order(order_id, symbol, params)


def fetch_open_orders(
    client: OKXExchangeClient, symbol: Optional[str] = None
) -> list[dict[str, Any]]:
    return client.fetch_open_orders(symbol)
