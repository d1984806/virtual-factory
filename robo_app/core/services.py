from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Literal

import pandas as pd

from robo_app.core.models import Settings, Suggestion, Trade
from robo_app.core.price_providers import PriceProvider


@dataclass
class Holding:
    symbol: str
    shares: float
    average_cost: float
    cost: float
    market_price: float
    market_value: float
    profit: float


@dataclass
class DashboardSummary:
    total_assets: float
    invested: float
    unrealized_pnl: float
    last_30_days: list[tuple[date, float]]


def compute_holdings(
    trades: Iterable[Trade],
    prices: dict[str, float],
    method: Literal["weighted", "fifo"] = "weighted",
) -> list[Holding]:
    if method == "fifo":
        return compute_holdings_fifo(trades, prices)
    return compute_holdings_weighted(trades, prices)


def compute_holdings_weighted(trades: Iterable[Trade], prices: dict[str, float]) -> list[Holding]:
    aggregation: dict[str, dict[str, float]] = {}
    for trade in trades:
        record = aggregation.setdefault(trade.symbol, {"shares": 0.0, "cost": 0.0})
        factor = 1 if trade.side == "BUY" else -1
        record["shares"] += trade.shares * factor
        record["cost"] += (trade.shares * trade.price + trade.fee + trade.tax) * factor

    holdings: list[Holding] = []
    for symbol, record in aggregation.items():
        shares = record["shares"]
        if shares == 0:
            continue
        cost = record["cost"]
        average_cost = cost / shares if shares else 0.0
        market_price = prices.get(symbol, 0.0)
        market_value = shares * market_price
        profit = market_value - cost
        holdings.append(
            Holding(
                symbol=symbol,
                shares=shares,
                average_cost=average_cost,
                cost=cost,
                market_price=market_price,
                market_value=market_value,
                profit=profit,
            )
        )
    return holdings


def compute_holdings_fifo(trades: Iterable[Trade], prices: dict[str, float]) -> list[Holding]:
    lots: dict[str, list[dict[str, float]]] = {}
    for trade in sorted(trades, key=lambda item: item.trade_date):
        symbol_lots = lots.setdefault(trade.symbol, [])
        if trade.side == "BUY":
            total_cost = trade.shares * trade.price + trade.fee + trade.tax
            symbol_lots.append({"shares": trade.shares, "cost": total_cost})
        else:
            remaining = trade.shares
            while remaining > 0 and symbol_lots:
                lot = symbol_lots[0]
                if lot["shares"] <= remaining:
                    remaining -= lot["shares"]
                    symbol_lots.pop(0)
                else:
                    lot_cost_per_share = lot["cost"] / lot["shares"]
                    lot["shares"] -= remaining
                    lot["cost"] -= lot_cost_per_share * remaining
                    remaining = 0
            if remaining > 0:
                symbol_lots.insert(0, {"shares": -remaining, "cost": -(remaining * trade.price)})

    holdings: list[Holding] = []
    for symbol, symbol_lots in lots.items():
        shares = sum(lot["shares"] for lot in symbol_lots)
        if shares == 0:
            continue
        cost = sum(lot["cost"] for lot in symbol_lots)
        average_cost = cost / shares if shares else 0.0
        market_price = prices.get(symbol, 0.0)
        market_value = shares * market_price
        profit = market_value - cost
        holdings.append(
            Holding(
                symbol=symbol,
                shares=shares,
                average_cost=average_cost,
                cost=cost,
                market_price=market_price,
                market_value=market_value,
                profit=profit,
            )
        )
    return holdings


def compute_dashboard_summary(
    trades: Iterable[Trade],
    holdings: list[Holding],
) -> DashboardSummary:
    invested = sum(trade.shares * trade.price + trade.fee + trade.tax for trade in trades if trade.side == "BUY")
    total_assets = sum(holding.market_value for holding in holdings)
    unrealized_pnl = sum(holding.profit for holding in holdings)

    today = date.today()
    last_30_days = [(today - timedelta(days=offset), total_assets) for offset in range(29, -1, -1)]
    return DashboardSummary(
        total_assets=total_assets,
        invested=invested,
        unrealized_pnl=unrealized_pnl,
        last_30_days=last_30_days,
    )


def load_settings_defaults(settings: Settings | None) -> Settings:
    if settings is None:
        return Settings(
            target_allocations=json.dumps({"006208": 0.6, "0050": 0.4}),
            cash=100000.0,
            max_daily_buy=50000.0,
            max_asset_ratio=0.6,
            min_cash=10000.0,
        )
    return settings


def parse_allocations(allocations_text: str) -> dict[str, float]:
    allocations: dict[str, float] = {}
    for line in allocations_text.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            continue
        symbol, percent = line.split(":", 1)
        allocations[symbol.strip()] = float(percent.strip()) / 100
    return allocations


def format_allocations(allocations: dict[str, float]) -> str:
    return "\n".join(f"{symbol}:{ratio * 100:.0f}" for symbol, ratio in allocations.items())


def rebalance_suggestions(
    holdings: list[Holding],
    settings: Settings,
    price_provider: PriceProvider,
) -> list[dict[str, float | str]]:
    allocations = json.loads(settings.target_allocations or "{}")
    if not allocations:
        return []

    prices = price_provider.bulk_prices(list(allocations.keys()))
    total_value = settings.cash + sum(holding.market_value for holding in holdings)
    suggestions: list[dict[str, float | str]] = []

    for symbol, target_ratio in allocations.items():
        target_value = total_value * float(target_ratio)
        current_shares = next((h.shares for h in holdings if h.symbol == symbol), 0.0)
        current_value = current_shares * prices.get(symbol, 0.0)
        diff_value = target_value - current_value
        price = prices.get(symbol, 0.0)
        if price == 0:
            continue
        shares_change = diff_value / price
        if shares_change > 0:
            shares_change = min(shares_change, settings.max_daily_buy / price)
        if target_ratio > settings.max_asset_ratio:
            continue
        if settings.cash - max(shares_change, 0) * price < settings.min_cash:
            continue
        suggestions.append(
            {
                "symbol": symbol,
                "action": "BUY" if shares_change > 0 else "SELL",
                "shares": round(shares_change, 2),
                "price": price,
                "target_ratio": float(target_ratio),
            }
        )

    return suggestions


def build_reports(
    trades: list[Trade],
    holdings: list[Holding],
    summary: DashboardSummary,
) -> dict[str, pd.DataFrame]:
    trades_df = pd.DataFrame(
        [
            {
                "date": trade.trade_date,
                "symbol": trade.symbol,
                "side": trade.side,
                "shares": trade.shares,
                "price": trade.price,
                "fee": trade.fee,
                "tax": trade.tax,
                "note": trade.note,
            }
            for trade in trades
        ]
    )
    holdings_df = pd.DataFrame(
        [
            {
                "symbol": holding.symbol,
                "shares": holding.shares,
                "average_cost": holding.average_cost,
                "cost": holding.cost,
                "market_price": holding.market_price,
                "market_value": holding.market_value,
                "profit": holding.profit,
            }
            for holding in holdings
        ]
    )
    summary_df = pd.DataFrame(
        [
            {
                "total_assets": summary.total_assets,
                "invested": summary.invested,
                "unrealized_pnl": summary.unrealized_pnl,
            }
        ]
    )
    return {
        "trades": trades_df,
        "holdings": holdings_df,
        "summary": summary_df,
    }


def serialize_suggestions(suggestions: list[dict[str, float | str]]) -> str:
    return json.dumps(suggestions, ensure_ascii=False, indent=2)
