from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TradingViewAlert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., description="buy, sell, or close")
    symbol: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0)
    timestamp: str = Field(..., min_length=1)
    timeframe: str = Field(..., min_length=1)
    strategy_name: str = Field(..., min_length=1)
    market_type: str = Field(..., min_length=1)
    leverage: int = Field(..., ge=1)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"buy", "sell", "close"}:
            raise ValueError("action must be one of: buy, sell, close")
        return normalized

    @field_validator("symbol", "timestamp", "timeframe", "strategy_name", "market_type")
    @classmethod
    def validate_text_field(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be empty")
        return cleaned

    @field_validator("market_type")
    @classmethod
    def validate_market_type(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized != "futures":
            raise ValueError("market_type must be futures")
        return normalized

    @field_validator("leverage")
    @classmethod
    def validate_leverage(cls, value: int) -> int:
        if value != 3:
            raise ValueError("leverage must be 3")
        return value
