from __future__ import annotations

import json
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication,
    QDateEdit,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from robo_app.core.database import session_scope
from robo_app.core.models import Suggestion


class DcaTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("DCA 定期定額"))

        form_layout = QFormLayout()
        self.day_input = QDateEdit()
        self.day_input.setDisplayFormat("dd")
        self.day_input.setDate(datetime.now())
        self.amount_input = QLineEdit()
        self.symbol_input = QLineEdit()
        self.slippage_input = QLineEdit()
        form_layout.addRow("每月扣款日", self.day_input)
        form_layout.addRow("每次金額", self.amount_input)
        form_layout.addRow("代號", self.symbol_input)
        form_layout.addRow("允許滑價%", self.slippage_input)
        self.layout.addLayout(form_layout)

        self.generate_button = QPushButton("產生本月建議")
        self.copy_button = QPushButton("複製提醒文字")
        self.layout.addWidget(self.generate_button)
        self.layout.addWidget(self.copy_button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.generate_button.clicked.connect(self.generate_suggestion)
        self.copy_button.clicked.connect(self.copy_to_clipboard)

    def generate_suggestion(self) -> None:
        context = self.window().context
        try:
            day = int(self.day_input.date().toString("dd"))
            amount = float(self.amount_input.text())
            symbol = self.symbol_input.text().strip().upper()
            slippage = float(self.slippage_input.text() or 0)
            if not symbol:
                raise ValueError("代號必填")
            if amount <= 0:
                raise ValueError("金額需大於 0")
        except ValueError as error:
            QMessageBox.warning(self, "輸入錯誤", str(error))
            return

        try:
            price = context.price_provider.get_price(symbol)
        except Exception as error:
            QMessageBox.warning(self, "價格取得失敗", str(error))
            return

        adjusted_price = price * (1 + slippage / 100)
        shares = int(amount // adjusted_price) if adjusted_price > 0 else 0
        estimated_cash = shares * adjusted_price
        risk_note = "OK" if shares > 0 else "金額不足以買入 1 股"

        suggestion = {
            "type": "DCA",
            "symbol": symbol,
            "day": day,
            "amount": amount,
            "slippage": slippage,
            "price": price,
            "adjusted_price": adjusted_price,
            "shares": shares,
            "estimated_cash": estimated_cash,
            "risk": risk_note,
        }

        with session_scope(context.session_factory) as session:
            context.suggestion_repo.add(session, Suggestion(content=json.dumps(suggestion, ensure_ascii=False)))

        message = (
            f"定期定額建議\n"
            f"代號: {symbol}\n"
            f"股數: {shares}\n"
            f"預估金額: {estimated_cash:,.2f}\n"
            f"風控結果: {risk_note}"
        )
        self.output.setPlainText(message)

    def copy_to_clipboard(self) -> None:
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "提示", "尚無可複製內容")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "完成", "已複製到剪貼簿")
