from __future__ import annotations

import logging
from typing import Any, Optional

from src.config import BotConfig
from src.exchange import OKXExchangeClient
from src.risk import RiskManager


logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(
        self,
        config: BotConfig,
        exchange_client: OKXExchangeClient,
        risk_manager: RiskManager,
    ):
        self.config = config
        self.exchange_client = exchange_client
        self.risk_manager = risk_manager

    def place_order(
        self,
        *,
        symbol: str,
        side: str,
        action: str,
        amount: float,
        state: dict[str, Any],
        equity: float,
        order_type: Optional[str] = None,
        price: Optional[float] = None,
        reason: str = "",
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        logger.info(
            "Intended order: symbol=%s side=%s action=%s type=%s amount=%.10f price=%s reason=%s dry_run=%s",
            symbol,
            side,
            action,
            order_type or self.config.default_order_type,
            amount,
            price,
            reason,
            self.config.dry_run,
        )

        if amount <= 0:
            return {"status": "rejected", "reason": "amount_must_be_positive"}

        allowed, risk_reason = self.risk_manager.pre_order_checks(action, state, equity)
        if not allowed:
            logger.warning("Order blocked by risk checks: %s", risk_reason)
            return {"status": "blocked", "reason": risk_reason}

        if self.config.dry_run:
            logger.info("DRY_RUN=1: create_order was not called")
            return {
                "status": "dry_run",
                "symbol": symbol,
                "side": side,
                "action": action,
                "amount": amount,
                "price": price,
                "reason": reason,
            }

        if self.config.kill_switch:
            logger.warning("Order blocked: KILL_SWITCH is active")
            return {"status": "blocked", "reason": "kill_switch_active"}

        return self.exchange_client.create_order(
            symbol=symbol,
            order_type=order_type or self.config.default_order_type,
            side=side,
            amount=amount,
            price=price,
            params=params or {},
        )
