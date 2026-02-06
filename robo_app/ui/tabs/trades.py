from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
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
from robo_app.core.models import Trade


class TradesTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.trade_date = QDateEdit()
        self.trade_date.setDate(date.today())
        self.trade_date.setCalendarPopup(True)
        self.symbol_input = QLineEdit()
        self.side_input = QComboBox()
        self.side_input.addItems(["BUY", "SELL"])
        self.shares_input = QLineEdit()
        self.price_input = QLineEdit()
        self.fee_input = QLineEdit()
        self.tax_input = QLineEdit()
        self.note_input = QLineEdit()

        self.form_layout.addRow("日期", self.trade_date)
        self.form_layout.addRow("代號", self.symbol_input)
        self.form_layout.addRow("買賣", self.side_input)
        self.form_layout.addRow("股數", self.shares_input)
        self.form_layout.addRow("價格", self.price_input)
        self.form_layout.addRow("手續費", self.fee_input)
        self.form_layout.addRow("稅", self.tax_input)
        self.form_layout.addRow("備註", self.note_input)

        self.layout.addLayout(self.form_layout)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("新增")
        self.update_button = QPushButton("更新")
        self.delete_button = QPushButton("刪除")
        self.refresh_button = QPushButton("重新整理")
        self.import_button = QPushButton("導入 CSV")
        self.export_button = QPushButton("匯出 CSV")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        self.layout.addLayout(button_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("篩選代號"))
        self.filter_input = QLineEdit()
        filter_layout.addWidget(self.filter_input)
        self.layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "日期",
            "代號",
            "買賣",
            "股數",
            "價格",
            "手續費",
            "稅",
            "備註",
        ])
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        self.add_button.clicked.connect(self.add_trade)
        self.update_button.clicked.connect(self.update_trade)
        self.delete_button.clicked.connect(self.delete_trade)
        self.refresh_button.clicked.connect(self.refresh)
        self.import_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_csv)
        self.filter_input.textChanged.connect(self.apply_filter)
        self.global_search_term = ""

        self.quick_add_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.quick_add_shortcut.activated.connect(self.add_trade)
        self.quick_add_shortcut_enter = QShortcut(QKeySequence("Ctrl+Enter"), self)
        self.quick_add_shortcut_enter.activated.connect(self.add_trade)

        self.refresh()

    def _context(self):
        return self.window().context

    def refresh(self) -> None:
        context = self._context()
        with session_scope(context.session_factory) as session:
            trades = context.trade_repo.list_all(session)
        self.table.setRowCount(len(trades))
        for row, trade in enumerate(trades):
            self.table.setItem(row, 0, QTableWidgetItem(str(trade.id)))
            self.table.setItem(row, 1, QTableWidgetItem(trade.trade_date.strftime("%Y-%m-%d")))
            self.table.setItem(row, 2, QTableWidgetItem(trade.symbol))
            self.table.setItem(row, 3, QTableWidgetItem(trade.side))
            self.table.setItem(row, 4, QTableWidgetItem(str(trade.shares)))
            self.table.setItem(row, 5, QTableWidgetItem(str(trade.price)))
            self.table.setItem(row, 6, QTableWidgetItem(str(trade.fee)))
            self.table.setItem(row, 7, QTableWidgetItem(str(trade.tax)))
            self.table.setItem(row, 8, QTableWidgetItem(trade.note))
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.filter_input.text().strip().upper()
        global_query = self.global_search_term.strip().upper()
        for row in range(self.table.rowCount()):
            symbol_item = self.table.item(row, 2)
            note_item = self.table.item(row, 8)
            symbol_text = symbol_item.text().upper() if symbol_item else ""
            note_text = note_item.text().upper() if note_item else ""
            matches_local = query in symbol_text if query else True
            matches_global = (
                (global_query in symbol_text) or (global_query in note_text)
                if global_query
                else True
            )
            self.table.setRowHidden(row, not (matches_local and matches_global))

    def set_global_search(self, term: str) -> None:
        self.global_search_term = term
        self.apply_filter()

    def _selected_trade_id(self) -> int | None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        return int(selected_items[0].text())

    def add_trade(self) -> None:
        try:
            trade = Trade(
                trade_date=self.trade_date.date().toPython(),
                symbol=self.symbol_input.text().strip().upper(),
                side=self.side_input.currentText(),
                shares=float(self.shares_input.text()),
                price=float(self.price_input.text()),
                fee=float(self.fee_input.text() or 0),
                tax=float(self.tax_input.text() or 0),
                note=self.note_input.text().strip(),
            )
            if not trade.symbol:
                raise ValueError("代號必填")
        except ValueError as error:
            QMessageBox.warning(self, "輸入錯誤", str(error))
            return

        context = self._context()
        with session_scope(context.session_factory) as session:
            context.trade_repo.add(session, trade)
        self.refresh()

    def update_trade(self) -> None:
        trade_id = self._selected_trade_id()
        if trade_id is None:
            QMessageBox.warning(self, "提示", "請選擇一筆交易")
            return
        context = self._context()
        with session_scope(context.session_factory) as session:
            trade = context.trade_repo.get(session, trade_id)
            if not trade:
                QMessageBox.warning(self, "錯誤", "交易不存在")
                return
            try:
                trade.trade_date = self.trade_date.date().toPython()
                trade.symbol = self.symbol_input.text().strip().upper()
                trade.side = self.side_input.currentText()
                trade.shares = float(self.shares_input.text())
                trade.price = float(self.price_input.text())
                trade.fee = float(self.fee_input.text() or 0)
                trade.tax = float(self.tax_input.text() or 0)
                trade.note = self.note_input.text().strip()
            except ValueError as error:
                QMessageBox.warning(self, "輸入錯誤", str(error))
                return
        self.refresh()

    def delete_trade(self) -> None:
        trade_id = self._selected_trade_id()
        if trade_id is None:
            QMessageBox.warning(self, "提示", "請選擇一筆交易")
            return
        context = self._context()
        with session_scope(context.session_factory) as session:
            context.trade_repo.delete(session, trade_id)
        self.refresh()

    def import_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇 CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        path = Path(file_path)
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    QMessageBox.warning(self, "錯誤", "CSV 欄位不存在")
                    return
                dialog = MappingDialog(reader.fieldnames, self)
                if dialog.exec() != QDialog.Accepted:
                    return
                mapping = dialog.mapping
                errors: list[str] = []
                trades: list[Trade] = []
                for index, row in enumerate(reader, start=2):
                    try:
                        trade = self._parse_row(row, mapping)
                        trades.append(trade)
                    except ValueError as error:
                        errors.append(f"第 {index} 列: {error}")
        except Exception as error:
            QMessageBox.critical(self, "錯誤", str(error))
            return

        context = self._context()
        with session_scope(context.session_factory) as session:
            for trade in trades:
                context.trade_repo.add(session, trade)

        self.refresh()
        if errors:
            error_dialog = ErrorReportDialog(errors, self)
            error_dialog.exec()
        else:
            QMessageBox.information(self, "完成", f"已匯入 {len(trades)} 筆交易")

    def export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "匯出 CSV", "trades.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        context = self._context()
        with session_scope(context.session_factory) as session:
            trades = context.trade_repo.list_all(session)
        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["date", "symbol", "side", "shares", "price", "fee", "tax", "note"])
                for trade in trades:
                    writer.writerow(
                        [
                            trade.trade_date.strftime("%Y-%m-%d"),
                            trade.symbol,
                            trade.side,
                            trade.shares,
                            trade.price,
                            trade.fee,
                            trade.tax,
                            trade.note,
                        ]
                    )
            QMessageBox.information(self, "完成", f"已匯出 {len(trades)} 筆")
        except Exception as error:
            QMessageBox.critical(self, "錯誤", str(error))

    def _parse_row(self, row: dict[str, str], mapping: dict[str, str]) -> Trade:
        trade_date = self._parse_date(row[mapping["trade_date"]])
        side = self._normalize_side(row[mapping["side"]])
        symbol = row[mapping["symbol"]].strip().upper()
        if not symbol:
            raise ValueError("代號必填")
        shares = float(row[mapping["shares"]])
        price = float(row[mapping["price"]])
        fee = float(row[mapping["fee"]]) if mapping.get("fee") else 0.0
        tax = float(row[mapping["tax"]]) if mapping.get("tax") else 0.0
        note = row[mapping["note"]].strip() if mapping.get("note") else ""
        return Trade(
            trade_date=trade_date,
            symbol=symbol,
            side=side,
            shares=shares,
            price=price,
            fee=fee,
            tax=tax,
            note=note,
        )

    def _parse_date(self, value: str) -> date:
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError("日期格式錯誤")

    def _normalize_side(self, value: str) -> str:
        value = value.strip().upper()
        mapping = {"B": "BUY", "BUY": "BUY", "買": "BUY", "S": "SELL", "SELL": "SELL", "賣": "SELL"}
        if value not in mapping:
            raise ValueError("買賣欄位不合法")
        return mapping[value]


class MappingDialog(QDialog):
    def __init__(self, headers: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("欄位對應")
        self.mapping: dict[str, str] = {}
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.fields: dict[str, QComboBox] = {}
        required = [
            ("trade_date", "日期"),
            ("symbol", "代號"),
            ("side", "買賣"),
            ("shares", "股數"),
            ("price", "價格"),
        ]
        optional = [
            ("fee", "手續費"),
            ("tax", "稅"),
            ("note", "備註"),
        ]
        for key, label in required + optional:
            combo = QComboBox()
            combo.addItems(headers)
            if key in {"fee", "tax", "note"}:
                combo.insertItem(0, "")
            guess = next((header for header in headers if header.lower() == key), None)
            if guess:
                combo.setCurrentText(guess)
            self.fields[key] = combo
            form_layout.addRow(label, combo)
        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        for key, combo in self.fields.items():
            selected = combo.currentText()
            if key in {"trade_date", "symbol", "side", "shares", "price"} and not selected:
                QMessageBox.warning(self, "錯誤", f"{key} 欄位必填")
                return
            if selected:
                self.mapping[key] = selected
        super().accept()


class ErrorReportDialog(QDialog):
    def __init__(self, errors: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("匯入錯誤報告")
        layout = QVBoxLayout(self)
        info = QLabel(f"共有 {len(errors)} 筆錯誤")
        layout.addWidget(info)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("\n".join(errors))
        layout.addWidget(text)
        close_button = QDialogButtonBox(QDialogButtonBox.Close)
        close_button.rejected.connect(self.reject)
        close_button.accepted.connect(self.accept)
        layout.addWidget(close_button)
