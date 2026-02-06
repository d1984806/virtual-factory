from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from robo_app.core.price_providers import MockPriceProvider, TwsePriceProvider


class PricesTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("價格來源"))
        self.provider_select = QComboBox()
        self.provider_select.addItems(["Mock", "TWSE"])
        self.layout.addWidget(self.provider_select)
        self.apply_button = QPushButton("套用")
        self.layout.addWidget(self.apply_button)
        self.preview_button = QPushButton("測試取得價格")
        self.layout.addWidget(self.preview_button)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.apply_button.clicked.connect(self.apply_provider)
        self.preview_button.clicked.connect(self.preview_prices)

    def apply_provider(self) -> None:
        context = self.window().context
        context.price_provider_name = self.provider_select.currentText()
        context.build_price_provider()
        QMessageBox.information(self, "完成", f"切換為 {context.price_provider.name}")

    def preview_prices(self) -> None:
        context = self.window().context
        symbols = ["0050", "006208"]
        try:
            prices = context.price_provider.bulk_prices(symbols)
        except Exception as error:
            QMessageBox.warning(self, "價格來源失敗", f"{error}\n改用 Mock")
            context.price_provider = MockPriceProvider(context.price_provider.cache)
            prices = context.price_provider.bulk_prices(symbols)
        output_lines = [f"{symbol}: {price:.2f}" for symbol, price in prices.items()]
        self.output.setPlainText("\n".join(output_lines))
