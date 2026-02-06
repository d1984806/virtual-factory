from __future__ import annotations

import importlib.util
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from robo_app.core.database import session_scope
from robo_app.core.services import compute_dashboard_summary, compute_holdings

QT_CHARTS_AVAILABLE = importlib.util.find_spec("PySide6.QtCharts") is not None
if QT_CHARTS_AVAILABLE:
    from PySide6.QtCharts import QChart, QChartView, QLineSeries
    from PySide6.QtGui import QPainter


class DashboardTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.summary_group = QGroupBox("總覽")
        self.summary_layout = QVBoxLayout(self.summary_group)
        self.total_assets_label = QLabel("總資產: 0")
        self.invested_label = QLabel("投入: 0")
        self.pnl_label = QLabel("未實現損益: 0")
        self.summary_layout.addWidget(self.total_assets_label)
        self.summary_layout.addWidget(self.invested_label)
        self.summary_layout.addWidget(self.pnl_label)
        self.layout.addWidget(self.summary_group)

        self.chart_group = QGroupBox("近 30 日資產變化")
        self.chart_layout = QVBoxLayout(self.chart_group)
        self.layout.addWidget(self.chart_group)

        self.refresh()

    def refresh(self) -> None:
        context = self.window().context
        with session_scope(context.session_factory) as session:
            trades = context.trade_repo.list_all(session)
            prices = context.price_provider.bulk_prices(list({trade.symbol for trade in trades}))
            holdings = compute_holdings(trades, prices)
            summary = compute_dashboard_summary(trades, holdings)

        self.total_assets_label.setText(f"總資產: {summary.total_assets:,.2f}")
        self.invested_label.setText(f"投入: {summary.invested:,.2f}")
        self.pnl_label.setText(f"未實現損益: {summary.unrealized_pnl:,.2f}")

        for index in reversed(range(self.chart_layout.count())):
            widget = self.chart_layout.itemAt(index).widget()
            if widget:
                widget.setParent(None)

        if QT_CHARTS_AVAILABLE:
            chart = QChart()
            series = QLineSeries()
            for offset, (day, value) in enumerate(summary.last_30_days):
                series.append(offset, value)
            chart.addSeries(series)
            chart.createDefaultAxes()
            chart.setTitle("近 30 日資產")
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            self.chart_layout.addWidget(chart_view)
        else:
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["日期", "資產"])
            table.setRowCount(len(summary.last_30_days))
            for row, (day, value) in enumerate(summary.last_30_days):
                table.setItem(row, 0, QTableWidgetItem(day.strftime("%Y-%m-%d")))
                item = QTableWidgetItem(f"{value:,.2f}")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 1, item)
            self.chart_layout.addWidget(table)
