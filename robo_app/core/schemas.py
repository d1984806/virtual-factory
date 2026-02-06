from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    trade_date: date
    symbol: str = Field(min_length=1)
    side: Literal["BUY", "SELL"]
    shares: float = Field(gt=0)
    price: float = Field(gt=0)
    fee: float = Field(ge=0, default=0)
    tax: float = Field(ge=0, default=0)
    note: str = Field(default="")


class TradeUpdate(TradeCreate):
    pass


class RebalanceSettings(BaseModel):
    target_allocations: dict[str, float]
    cash: float = Field(ge=0)
    max_daily_buy: float = Field(ge=0)
    max_asset_ratio: float = Field(ge=0, le=1)
    min_cash: float = Field(ge=0)
