from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

import requests


class PriceProvider(Protocol):
    name: str

    def get_price(self, symbol: str) -> float:
        ...

    def bulk_prices(self, symbols: list[str]) -> dict[str, float]:
        ...


@dataclass
class PriceCache:
    path: Path

    def load(self) -> dict[str, float]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save(self, prices: dict[str, float]) -> None:
        self.path.write_text(json.dumps(prices, ensure_ascii=False, indent=2), encoding="utf-8")


class MockPriceProvider:
    name = "Mock"

    def __init__(self, cache: PriceCache | None = None) -> None:
        self.cache = cache

    def get_price(self, symbol: str) -> float:
        prices = self.cache.load() if self.cache else {}
        if symbol in prices:
            return float(prices[symbol])
        price = round(random.uniform(20, 200), 2)
        prices[symbol] = price
        if self.cache:
            self.cache.save(prices)
        return price

    def bulk_prices(self, symbols: list[str]) -> dict[str, float]:
        return {symbol: self.get_price(symbol) for symbol in symbols}


class TwsePriceProvider:
    name = "TWSE"

    def __init__(self, cache: PriceCache | None = None) -> None:
        self.cache = cache

    def get_price(self, symbol: str) -> float:
        prices = self.bulk_prices([symbol])
        return prices[symbol]

    def bulk_prices(self, symbols: list[str]) -> dict[str, float]:
        prices: dict[str, float] = {}
        for symbol in symbols:
            prices[symbol] = self._fetch_price(symbol)
        return prices

    def _fetch_price(self, symbol: str) -> float:
        url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
        params = {"response": "json", "stockNo": symbol, "date": datetime.now().strftime("%Y%m%d")}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if payload.get("stat") != "OK":
            raise ValueError("TWSE response not OK")
        data = payload.get("data", [])
        if not data:
            raise ValueError("No price data")
        last_row = data[-1]
        price_str = last_row[6].replace(",", "")
        price = float(price_str)
        if self.cache:
            cached = self.cache.load()
            cached[symbol] = price
            self.cache.save(cached)
        return price


def build_price_provider(
    provider_name: str,
    cache_path: Path,
) -> PriceProvider:
    cache = PriceCache(cache_path)
    if provider_name == "TWSE":
        return TwsePriceProvider(cache)
    return MockPriceProvider(cache)
