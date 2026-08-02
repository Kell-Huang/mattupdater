from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QApplication
)
from PySide6.QtGui import QFont, QTextCursor


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("logPanel")
        self.setStyleSheet(
            "QWidget#logPanel { background-color: #2D1B3D; border: 1px solid #5A3D6B; border-radius: 6px; }"
        )
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        title_label = QLabel("LOG")
        title_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #FFFFFF; "
            "text-transform: uppercase;"
        )
        layout.addWidget(title_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 11))
        self.log_text.setStyleSheet(
            "background-color: #1E1228; color: #FFFFFF; "
            "border: 1px solid #5A3D6B; border-radius: 4px; "
            "padding: 8px; font-family: Consolas, monospace;"
        )
        layout.addWidget(self.log_text, stretch=1)

    def _timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def _append(self, prefix, message, color="#FFFFFF"):
        timestamp = self._timestamp()
        line = f"[{timestamp}] {prefix:4s} {message}"
        self.log_text.append(
            f'<span style="color: {color};">{line}</span>'
        )
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        QApplication.processEvents()

    def info(self, message):
        self._append("INFO", message, "#FFFFFF")

    def success(self, message):
        self._append("OK  ", message, "#27AE60")

    def warning(self, message):
        self._append("WARN", message, "#F39C12")

    def error(self, message):
        self._append("ERR ", message, "#E74C3C")

    def step(self, step_name, duration):
        self._append("STEP", f"{step_name:<35} {duration:.1f}s", "#A08DB5")

    def clear(self):
        self.log_text.clear()

    def get_text(self):
        return self.log_text.toPlainText()