from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


class LogsTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("日誌視窗"))
        self.refresh_button = QPushButton("重新整理")
        self.layout.addWidget(self.refresh_button)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.layout.addWidget(self.text_area)

        self.refresh_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        context = self.window().context
        log_path = Path(context.paths.logs_dir) / "app.log"
        if not log_path.exists():
            self.text_area.setPlainText("尚無日誌")
            return
        content = log_path.read_text(encoding="utf-8")
        lines = content.splitlines()[-200:]
        self.text_area.setPlainText("\n".join(lines))
