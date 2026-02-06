from __future__ import annotations

import unittest
from datetime import date

try:
    import sqlalchemy  # noqa: F401

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

if SQLALCHEMY_AVAILABLE:
    from robo_app.core.models import Trade
    from robo_app.core.services import compute_holdings, compute_holdings_fifo, compute_holdings_weighted


@unittest.skipUnless(SQLALCHEMY_AVAILABLE, "sqlalchemy not installed")
class HoldingsComputationTests(unittest.TestCase):
    def test_compute_holdings_weighted(self) -> None:
        trades = [
            Trade(trade_date=date(2024, 1, 1), symbol="0050", side="BUY", shares=10, price=100, fee=0, tax=0),
            Trade(trade_date=date(2024, 1, 2), symbol="0050", side="BUY", shares=10, price=110, fee=0, tax=0),
        ]
        prices = {"0050": 120.0}
        holdings = compute_holdings_weighted(trades, prices)
        self.assertEqual(len(holdings), 1)
        holding = holdings[0]
        self.assertAlmostEqual(holding.shares, 20)
        self.assertAlmostEqual(holding.average_cost, 105)
        self.assertAlmostEqual(holding.market_value, 2400)

    def test_compute_holdings_fifo(self) -> None:
        trades = [
            Trade(trade_date=date(2024, 1, 1), symbol="0050", side="BUY", shares=10, price=100, fee=0, tax=0),
            Trade(trade_date=date(2024, 1, 2), symbol="0050", side="BUY", shares=10, price=110, fee=0, tax=0),
            Trade(trade_date=date(2024, 1, 3), symbol="0050", side="SELL", shares=5, price=120, fee=0, tax=0),
        ]
        prices = {"0050": 120.0}
        holdings = compute_holdings_fifo(trades, prices)
        self.assertEqual(len(holdings), 1)
        holding = holdings[0]
        self.assertAlmostEqual(holding.shares, 15)
        self.assertAlmostEqual(holding.average_cost, 103.3333333333, places=4)

    def test_compute_holdings_dispatch(self) -> None:
        trades = [
            Trade(trade_date=date(2024, 1, 1), symbol="006208", side="BUY", shares=5, price=50, fee=0, tax=0),
        ]
        prices = {"006208": 55.0}
        holdings = compute_holdings(trades, prices, method="fifo")
        self.assertEqual(holdings[0].symbol, "006208")


if __name__ == "__main__":
    unittest.main()
