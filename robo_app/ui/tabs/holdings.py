from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from robo_app.core.database import session_scope
from robo_app.core.services import compute_holdings


class HoldingsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.info_label = QLabel("持倉列表")
        self.layout.addWidget(self.info_label)
        self.method_select = QComboBox()
        self.method_select.addItems(["加權平均", "FIFO"])
        self.layout.addWidget(self.method_select)
        self.refresh_button = QPushButton("重新計算")
        self.layout.addWidget(self.refresh_button)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "代號",
            "股數",
            "均價",
            "成本",
            "市價",
            "市值",
            "損益",
        ])
        self.layout.addWidget(self.table)

        self.refresh_button.clicked.connect(self.refresh)
        self.method_select.currentTextChanged.connect(self.refresh)
        self.global_search_term = ""
        self.refresh()

    def refresh(self) -> None:
        context = self.window().context
        try:
            with session_scope(context.session_factory) as session:
                trades = context.trade_repo.list_all(session)
            prices = context.price_provider.bulk_prices(list({trade.symbol for trade in trades}))
            method = "fifo" if self.method_select.currentText() == "FIFO" else "weighted"
            holdings = compute_holdings(trades, prices, method=method)
        except Exception as error:
            QMessageBox.critical(self, "錯誤", str(error))
            return

        self.table.setRowCount(len(holdings))
        for row, holding in enumerate(holdings):
            self.table.setItem(row, 0, QTableWidgetItem(holding.symbol))
            self.table.setItem(row, 1, QTableWidgetItem(f"{holding.shares:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{holding.average_cost:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{holding.cost:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{holding.market_price:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{holding.market_value:.2f}"))
            item = QTableWidgetItem(f"{holding.profit:.2f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 6, item)

        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.global_search_term.strip().upper()
        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, 0)
            symbol_text = symbol_item.text().upper() if symbol_item else ""
            matches = query in symbol_text if query else True
            self.table.setRowHidden(row, not matches)

    def set_global_search(self, term: str) -> None:
        self.global_search_term = term
        self.apply_filter()
