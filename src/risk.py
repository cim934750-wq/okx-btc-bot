from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.config import BotConfig


logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self, config: BotConfig):
        self.config = config

    def stop_price_for_long(self, entry_price: float, atr: float) -> float:
        return entry_price - self.stop_distance(atr)

    def stop_distance(self, atr: float) -> float:
        return max(float(atr) * self.config.atr_stop_multiplier, 0.0)

    def position_size(self, equity: float, entry_price: float, atr: float) -> float:
        stop_distance = self.stop_distance(atr)
        if equity <= 0 or entry_price <= 0 or stop_distance <= 0:
            return 0.0

        risk_budget = equity * self.config.max_risk_per_trade
        risk_based_size = risk_budget / stop_distance
        max_affordable_size = (equity * 0.95) / entry_price
        return max(min(risk_based_size, max_affordable_size), 0.0)

    def refresh_loss_windows(self, state: dict[str, Any], equity: float) -> None:
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        month = now.strftime("%Y-%m")

        if state.get("daily_start_date") != today:
            state["daily_start_date"] = today
            state["daily_start_equity"] = equity
            state["daily_entries_blocked"] = False

        if state.get("monthly_start_month") != month and not state.get(
            "monthly_entries_blocked"
        ):
            state["monthly_start_month"] = month
            state["monthly_start_equity"] = equity
            state["monthly_entries_blocked"] = False

    def daily_loss_breached(self, state: dict[str, Any], equity: float) -> bool:
        baseline = float(state.get("daily_start_equity") or equity or 0.0)
        if baseline <= 0:
            return False
        breached = (baseline - equity) / baseline >= self.config.max_daily_loss
        if breached:
            state["daily_entries_blocked"] = True
        return breached

    def monthly_loss_breached(self, state: dict[str, Any], equity: float) -> bool:
        baseline = float(state.get("monthly_start_equity") or equity or 0.0)
        if baseline <= 0:
            return False
        breached = (baseline - equity) / baseline >= self.config.max_monthly_loss
        if breached:
            state["monthly_entries_blocked"] = True
        return breached

    def can_enter_new_position(
        self, state: dict[str, Any], equity: float
    ) -> tuple[bool, str]:
        if self.config.kill_switch:
            return False, "kill_switch_active"
        if self.daily_loss_breached(state, equity):
            return False, "max_daily_loss_breached"
        if self.monthly_loss_breached(state, equity):
            return False, "max_monthly_loss_breached"
        if state.get("daily_entries_blocked"):
            return False, "daily_entries_blocked"
        if state.get("monthly_entries_blocked"):
            return False, "monthly_entries_blocked"
        return True, "risk_checks_passed"

    def pre_order_checks(
        self,
        action: str,
        state: dict[str, Any],
        equity: float,
    ) -> tuple[bool, str]:
        if self.config.kill_switch:
            return False, "kill_switch_active"
        if action in {"entry", "long_entry", "buy"}:
            return self.can_enter_new_position(state, equity)
        return True, "risk_checks_passed"
