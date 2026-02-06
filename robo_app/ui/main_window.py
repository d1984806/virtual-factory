from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from robo_app.ui.tabs.dashboard import DashboardTab
from robo_app.ui.tabs.dca import DcaTab
from robo_app.ui.tabs.holdings import HoldingsTab
from robo_app.ui.tabs.logs import LogsTab
from robo_app.ui.tabs.prices import PricesTab
from robo_app.ui.tabs.rebalance import RebalanceTab
from robo_app.ui.tabs.reports import ReportsTab
from robo_app.ui.tabs.trades import TradesTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Robo Desktop TW")
        self.resize(1200, 800)

        container = QWidget()
        layout = QVBoxLayout(container)

        header_layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("全站搜尋"))
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        header_layout.addLayout(search_layout)
        self.update_label = QLabel("資料更新時間: --")
        self.update_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.update_label)
        layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab(self)
        self.trades_tab = TradesTab(self)
        self.holdings_tab = HoldingsTab(self)
        self.dca_tab = DcaTab(self)
        self.prices_tab = PricesTab(self)
        self.rebalance_tab = RebalanceTab(self)
        self.reports_tab = ReportsTab(self)
        self.logs_tab = LogsTab(self)

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.trades_tab, "Trades")
        self.tabs.addTab(self.holdings_tab, "Holdings")
        self.tabs.addTab(self.dca_tab, "DCA")
        self.tabs.addTab(self.prices_tab, "Prices")
        self.tabs.addTab(self.rebalance_tab, "Rebalance")
        self.tabs.addTab(self.reports_tab, "Reports")
        self.tabs.addTab(self.logs_tab, "Logs")

        layout.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_timestamp)
        self.update_timer.start(60_000)
        self.refresh_timestamp()

        self.search_input.textChanged.connect(self.apply_global_search)

    def refresh_timestamp(self) -> None:
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.update_label.setText(f"資料更新時間: {now_text}")

    def apply_global_search(self, term: str) -> None:
        for tab in (
            self.trades_tab,
            self.holdings_tab,
            self.rebalance_tab,
        ):
            if hasattr(tab, "set_global_search"):
                tab.set_global_search(term)
