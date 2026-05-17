import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status

from server.config import Settings
from server.models import TradingViewAlert


logger = logging.getLogger("webhook.okx")


class OKXClient:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.okx_api_key
        self.secret_key = settings.okx_secret_key
        self.passphrase = settings.okx_passphrase
        self.base_url = settings.okx_base_url
        self.trade_mode = settings.okx_trade_mode
        self.default_size = settings.okx_default_size
        self.timeout_seconds = settings.http_timeout_seconds

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _sign(self, timestamp: str, method: str, request_path: str, body: str) -> str:
        prehash = f"{timestamp}{method.upper()}{request_path}{body}"
        digest = hmac.new(
            self.secret_key.encode("utf-8"),
            prehash.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    async def _request(self, method: str, request_path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, separators=(",", ":"))
        timestamp = self._timestamp()
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self._sign(timestamp, method, request_path, body),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{request_path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.request(method.upper(), url, headers=headers, content=body)
        except httpx.HTTPError as exc:
            logger.exception("Network error while contacting OKX")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="network error while contacting OKX",
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.error("Non-JSON response from OKX: %s", response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OKX returned a non-JSON response",
            ) from exc

        if response.status_code >= 400:
            logger.error("OKX HTTP error status=%s response=%s", response.status_code, data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OKX HTTP error",
            )

        if data.get("code") != "0":
            logger.error("OKX API rejected request response=%s", data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OKX API rejected request",
            )

        return data

    async def set_leverage(self, *, inst_id: str, leverage: int, pos_side: str) -> dict[str, Any]:
        payload = {
            "instId": inst_id,
            "lever": str(leverage),
            "mgnMode": self.trade_mode,
            "posSide": pos_side,
        }
        return await self._request("POST", "/api/v5/account/set-leverage", payload)

    async def get_positions(self, *, inst_id: str) -> list[dict[str, Any]]:
        request_path = f"/api/v5/account/positions?instId={inst_id}"
        timestamp = self._timestamp()
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self._sign(timestamp, "GET", request_path, ""),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
        }

        url = f"{self.base_url}{request_path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("Network error while fetching OKX positions")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="network error while contacting OKX",
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.error("Non-JSON response from OKX positions endpoint: %s", response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OKX returned a non-JSON response",
            ) from exc

        if response.status_code >= 400 or data.get("code") != "0":
            logger.error("Failed to fetch OKX positions status=%s response=%s", response.status_code, data)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="failed to fetch OKX positions",
            )

        return data.get("data", [])

    async def execute_alert(self, alert: TradingViewAlert) -> dict[str, Any]:
        inst_id = alert.symbol
        size = self.default_size

        if alert.action == "buy":
            leverage_response = await self.set_leverage(inst_id=inst_id, leverage=alert.leverage, pos_side="long")
            order_response = await self.place_market_order(inst_id=inst_id, side="buy", pos_side="long", size=size)
            return {"set_leverage": leverage_response, "order": order_response}
        if alert.action == "sell":
            leverage_response = await self.set_leverage(inst_id=inst_id, leverage=alert.leverage, pos_side="short")
            order_response = await self.place_market_order(inst_id=inst_id, side="sell", pos_side="short", size=size)
            return {"set_leverage": leverage_response, "order": order_response}
        return await self.close_all_positions(inst_id=inst_id)

    async def place_market_order(self, *, inst_id: str, side: str, pos_side: str, size: str) -> dict[str, Any]:
        payload = {
            "instId": inst_id,
            "tdMode": self.trade_mode,
            "side": side,
            "ordType": "market",
            "sz": size,
            "posSide": pos_side,
            "clOrdId": uuid.uuid4().hex[:32],
        }
        return await self._request("POST", "/api/v5/trade/order", payload)

    async def close_position(self, *, inst_id: str) -> dict[str, Any]:
        payload = {
            "instId": inst_id,
            "mgnMode": self.trade_mode,
            "autoCxl": True,
            "clOrdId": uuid.uuid4().hex[:32],
        }
        return await self._request("POST", "/api/v5/trade/close-position", payload)

    async def close_position_side(self, *, inst_id: str, pos_side: str) -> dict[str, Any]:
        payload = {
            "instId": inst_id,
            "mgnMode": self.trade_mode,
            "posSide": pos_side,
            "autoCxl": True,
            "clOrdId": uuid.uuid4().hex[:32],
        }
        return await self._request("POST", "/api/v5/trade/close-position", payload)

    async def close_all_positions(self, *, inst_id: str) -> dict[str, Any]:
        positions = await self.get_positions(inst_id=inst_id)
        active_sides: list[str] = []
        for position in positions:
            pos_side = str(position.get("posSide", "")).lower()
            pos_size = position.get("pos")
            try:
                size_value = abs(float(pos_size))
            except (TypeError, ValueError):
                size_value = 0.0
            if pos_side in {"long", "short"} and size_value > 0:
                active_sides.append(pos_side)

        if not active_sides:
            return {"message": "no open position to close", "instId": inst_id, "closed": []}

        responses = []
        for pos_side in active_sides:
            responses.append(await self.close_position_side(inst_id=inst_id, pos_side=pos_side))

        return {"instId": inst_id, "closed": responses}
