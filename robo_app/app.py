from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from robo_app.core.config import build_paths, ensure_directories, load_environment
from robo_app.core.database import Base, build_session_factory, create_engine_instance, ensure_trade_note_column
from robo_app.core.price_providers import build_price_provider
from robo_app.core.repositories import (
    AnalyticsRepository,
    CashflowRepository,
    SettingsRepository,
    SuggestionRepository,
    TradeRepository,
)
from robo_app.core.utils import setup_logging
from robo_app.ui.main_window import MainWindow


class AppContext:
    def __init__(self, root_dir: Path) -> None:
        load_environment()
        self.paths = build_paths(root_dir)
        ensure_directories(self.paths)
        setup_logging(self.paths.logs_dir)
        engine = create_engine_instance(str(self.paths.db_path))
        Base.metadata.create_all(engine)
        ensure_trade_note_column(engine)
        self.session_factory = build_session_factory(engine)
        self.trade_repo = TradeRepository()
        self.cashflow_repo = CashflowRepository()
        self.settings_repo = SettingsRepository()
        self.suggestion_repo = SuggestionRepository()
        self.analytics_repo = AnalyticsRepository()
        self.price_provider_name = "Mock"

    def build_price_provider(self) -> None:
        self.price_provider = build_price_provider(self.price_provider_name, self.paths.price_cache_path)


class RoboApp(QApplication):
    def __init__(self, root_dir: Path) -> None:
        super().__init__(sys.argv)
        self.context = AppContext(root_dir)
        self.context.build_price_provider()
        self.window = MainWindow()
        self.window.context = self.context
        self.window.show()


    def notify_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self.window, title, message)


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    app = RoboApp(root_dir)
    sys.exit(app.exec())
