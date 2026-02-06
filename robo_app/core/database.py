from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def create_engine_instance(db_path: str) -> Engine:
    return create_engine(f"sqlite:///{db_path}", echo=False, future=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def ensure_trade_note_column(engine: Engine) -> None:
    with engine.begin() as connection:
        result = connection.execute(text("PRAGMA table_info(trades)"))
        columns = {row[1] for row in result.fetchall()}
        if "note" not in columns:
            connection.execute(text("ALTER TABLE trades ADD COLUMN note VARCHAR(255) DEFAULT ''"))


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
