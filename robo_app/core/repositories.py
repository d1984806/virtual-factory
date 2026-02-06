from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from robo_app.core.models import Cashflow, Settings, Suggestion, Trade


class TradeRepository:
    def list_all(self, session: Session) -> list[Trade]:
        return list(session.scalars(select(Trade).order_by(Trade.trade_date.desc(), Trade.id.desc())))

    def add(self, session: Session, trade: Trade) -> None:
        session.add(trade)

    def delete(self, session: Session, trade_id: int) -> None:
        trade = session.get(Trade, trade_id)
        if trade:
            session.delete(trade)

    def get(self, session: Session, trade_id: int) -> Trade | None:
        return session.get(Trade, trade_id)


class CashflowRepository:
    def list_all(self, session: Session) -> list[Cashflow]:
        return list(session.scalars(select(Cashflow).order_by(Cashflow.flow_date.desc())))

    def add(self, session: Session, cashflow: Cashflow) -> None:
        session.add(cashflow)


class SuggestionRepository:
    def add(self, session: Session, suggestion: Suggestion) -> None:
        session.add(suggestion)


class SettingsRepository:
    def get_latest(self, session: Session) -> Settings | None:
        return session.scalar(select(Settings).order_by(Settings.updated_at.desc()))

    def save(self, session: Session, settings: Settings) -> None:
        session.add(settings)


class AnalyticsRepository:
    def trades_since(self, session: Session, start_date: date) -> list[Trade]:
        return list(session.scalars(select(Trade).where(Trade.trade_date >= start_date)))
