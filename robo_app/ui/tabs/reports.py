from __future__ import annotations

import contextlib
from datetime import datetime

import pandas as pd

from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from robo_app.core.database import session_scope
from robo_app.core.services import build_reports, compute_dashboard_summary, compute_holdings


class ReportsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("匯出 Excel 報表"))
        self.export_button = QPushButton("一鍵匯出")
        self.layout.addWidget(self.export_button)
        self.export_button.clicked.connect(self.export_reports)

    def export_reports(self) -> None:
        context = self.window().context
        try:
            with session_scope(context.session_factory) as session:
                trades = context.trade_repo.list_all(session)
            prices = context.price_provider.bulk_prices(list({trade.symbol for trade in trades}))
            holdings = compute_holdings(trades, prices)
            summary = compute_dashboard_summary(trades, holdings)
            reports = build_reports(trades, holdings, summary)

            timestamp = datetime.now().strftime("%Y%m%d")
            export_path = context.paths.exports_dir / f"report_{timestamp}.xlsx"
            with contextlib.ExitStack() as stack:
                writer = stack.enter_context(pd.ExcelWriter(export_path, engine="openpyxl"))
                for name, frame in reports.items():
                    frame.to_excel(writer, sheet_name=name, index=False)
            QMessageBox.information(self, "完成", f"已匯出 {export_path}")
        except Exception as error:
            QMessageBox.critical(self, "錯誤", str(error))
