from __future__ import annotations

import json
from datetime import datetime

from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from robo_app.core.database import session_scope
from robo_app.core.models import Settings, Suggestion
from robo_app.core.services import (
    compute_holdings,
    format_allocations,
    load_settings_defaults,
    parse_allocations,
    rebalance_suggestions,
    serialize_suggestions,
)


class RebalanceTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("目標配置 (格式: 代號:百分比)"))
        self.allocations_input = QTextEdit()
        self.layout.addWidget(self.allocations_input)

        form_layout = QFormLayout()
        self.cash_input = QLineEdit()
        self.max_daily_buy_input = QLineEdit()
        self.max_asset_ratio_input = QLineEdit()
        self.min_cash_input = QLineEdit()
        form_layout.addRow("現金", self.cash_input)
        form_layout.addRow("單日買入上限", self.max_daily_buy_input)
        form_layout.addRow("單一標的上限(比例)", self.max_asset_ratio_input)
        form_layout.addRow("現金下限", self.min_cash_input)
        self.layout.addLayout(form_layout)

        self.save_button = QPushButton("儲存設定")
        self.calculate_button = QPushButton("計算")
        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.calculate_button)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "代號",
            "動作",
            "股數",
            "價格",
            "目標比例",
        ])
        self.layout.addWidget(self.table)

        self.save_button.clicked.connect(self.save_settings)
        self.calculate_button.clicked.connect(self.calculate)
        self.global_search_term = ""

        self.load_settings()

    def load_settings(self) -> None:
        context = self.window().context
        with session_scope(context.session_factory) as session:
            settings = load_settings_defaults(context.settings_repo.get_latest(session))
        allocations = json.loads(settings.target_allocations or "{}")
        self.allocations_input.setPlainText(format_allocations(allocations))
        self.cash_input.setText(str(settings.cash))
        self.max_daily_buy_input.setText(str(settings.max_daily_buy))
        self.max_asset_ratio_input.setText(str(settings.max_asset_ratio))
        self.min_cash_input.setText(str(settings.min_cash))

    def save_settings(self) -> None:
        context = self.window().context
        try:
            allocations = parse_allocations(self.allocations_input.toPlainText())
            settings = Settings(
                updated_at=datetime.utcnow(),
                target_allocations=json.dumps(allocations, ensure_ascii=False),
                cash=float(self.cash_input.text()),
                max_daily_buy=float(self.max_daily_buy_input.text()),
                max_asset_ratio=float(self.max_asset_ratio_input.text()),
                min_cash=float(self.min_cash_input.text()),
            )
        except ValueError as error:
            QMessageBox.warning(self, "輸入錯誤", str(error))
            return

        with session_scope(context.session_factory) as session:
            context.settings_repo.save(session, settings)
        QMessageBox.information(self, "完成", "設定已儲存")

    def calculate(self) -> None:
        context = self.window().context
        try:
            with session_scope(context.session_factory) as session:
                trades = context.trade_repo.list_all(session)
                settings = load_settings_defaults(context.settings_repo.get_latest(session))
            prices = context.price_provider.bulk_prices(list({trade.symbol for trade in trades}))
            holdings = compute_holdings(trades, prices)
            suggestions = rebalance_suggestions(holdings, settings, context.price_provider)

            with session_scope(context.session_factory) as session:
                context.suggestion_repo.add(session, Suggestion(content=serialize_suggestions(suggestions)))
        except Exception as error:
            QMessageBox.critical(self, "錯誤", str(error))
            return

        self.table.setRowCount(len(suggestions))
        for row, suggestion in enumerate(suggestions):
            self.table.setItem(row, 0, QTableWidgetItem(str(suggestion["symbol"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(suggestion["action"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(suggestion["shares"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(suggestion["price"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(suggestion["target_ratio"])))
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
