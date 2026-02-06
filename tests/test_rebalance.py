from __future__ import annotations

import json
import unittest
from datetime import date

try:
    import sqlalchemy  # noqa: F401

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

if SQLALCHEMY_AVAILABLE:
    from robo_app.core.models import Settings, Trade
    from robo_app.core.services import compute_holdings, rebalance_suggestions


class DummyPriceProvider:
    name = "Dummy"

    def __init__(self, prices: dict[str, float]) -> None:
        self._prices = prices

    def get_price(self, symbol: str) -> float:
        return self._prices[symbol]

    def bulk_prices(self, symbols: list[str]) -> dict[str, float]:
        return {symbol: self._prices[symbol] for symbol in symbols}


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy not installed")
class RebalanceSuggestionTests(unittest.TestCase):
    def test_rebalance_generates_suggestions(self) -> None:
        trades = [
            Trade(trade_date=date(2024, 1, 1), symbol="0050", side="BUY", shares=10, price=100, fee=0, tax=0),
        ]
        prices = {"0050": 100.0, "006208": 50.0}
        holdings = compute_holdings(trades, {"0050": 100.0})
        settings = Settings(
            target_allocations=json.dumps({"0050": 0.5, "006208": 0.5}),
            cash=1000.0,
            max_daily_buy=1000.0,
            max_asset_ratio=0.8,
            min_cash=0.0,
        )
        provider = DummyPriceProvider(prices)

        suggestions = rebalance_suggestions(holdings, settings, provider)
        symbols = {item["symbol"] for item in suggestions}
        self.assertIn("006208", symbols)


if __name__ == "__main__":
    unittest.main()
