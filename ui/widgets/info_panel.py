import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt


class InfoCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("infoCard")
        self.setStyleSheet(
            "QFrame#infoCard { background-color: #3D2A50; border: 1px solid #5A3D6B; border-radius: 6px; }"
        )
        self._value_labels = {}
        self.init_ui(title)

    def init_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #FFFFFF;"
            "text-transform: uppercase;"
        )
        layout.addWidget(title_label)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(4)
        layout.addLayout(self.content_layout)

    def add_info_row(self, key, label_text):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 2, 0, 2)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 12px; color: #D4C4E0;")

        val = QLabel("-")
        val.setStyleSheet("font-size: 12px; font-weight: 600; color: #FFFFFF;")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        row_layout.addWidget(lbl)
        row_layout.addWidget(val, stretch=1)

        self.content_layout.addWidget(row)
        self._value_labels[key] = val
        return val

    def set_value(self, key, value):
        if key in self._value_labels:
            self._value_labels[key].setText(str(value))


class StatusCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("infoCard")
        self.setStyleSheet(
            "QFrame#infoCard { background-color: #3D2A50; border: 1px solid #5A3D6B; border-radius: 6px; }"
        )
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel("STATUS")
        title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #FFFFFF;"
            "text-transform: uppercase;"
        )
        layout.addWidget(title)

        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #FFFFFF; padding: 8px 12px;"
            "background-color: #2D1B3D;"
            "border-left: 4px solid #27AE60;"
            "border-radius: 4px;"
        )
        layout.addWidget(self.status_label)

        self.formula_label = QLabel("")
        self.formula_label.setWordWrap(True)
        self.formula_label.setStyleSheet("font-size: 11px; color: #D4C4E0;")
        self.formula_label.hide()
        layout.addWidget(self.formula_label)

        layout.addStretch()

    def set_ready(self, formula_count=0):
        self.status_label.setText("Ready - Click Execute to start")
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #FFFFFF; padding: 8px 12px;"
            "background-color: #2D1B3D;"
            "border-left: 4px solid #27AE60;"
            "border-radius: 4px;"
        )
        if formula_count > 0:
            self.formula_label.setText(
                f"Detected {formula_count} formula column(s) - will be auto-restored"
            )
            self.formula_label.show()
        else:
            self.formula_label.hide()

    def set_running(self):
        self.status_label.setText("Running...")
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #FFFFFF; padding: 8px 12px;"
            "background-color: #2D1B3D;"
            "border-left: 4px solid #F39C12;"
            "border-radius: 4px;"
        )

    def set_done(self):
        self.status_label.setText("Update completed successfully")
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #FFFFFF; padding: 8px 12px;"
            "background-color: #2D1B3D;"
            "border-left: 4px solid #27AE60;"
            "border-radius: 4px;"
        )

    def set_error(self, msg=""):
        display = f"Error: {msg}" if msg else "Error occurred"
        self.status_label.setText(display)
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #FFFFFF; padding: 8px 12px;"
            "background-color: #2D1B3D;"
            "border-left: 4px solid #E74C3C;"
            "border-radius: 4px;"
        )


class InfoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.source_card = InfoCard("Source File Info")
        self.source_rows_label = self.source_card.add_info_row("rows", "Rows")
        self.source_cols_label = self.source_card.add_info_row("cols", "Columns")
        self.source_size_label = self.source_card.add_info_row("size", "Size")
        layout.addWidget(self.source_card)

        self.target_card = InfoCard("Target File Info")
        self.target_rows_label = self.target_card.add_info_row("rows", "Rows")
        self.target_cols_label = self.target_card.add_info_row("cols", "Columns")
        self.target_size_label = self.target_card.add_info_row("size", "Size")
        layout.addWidget(self.target_card)

        self.status = StatusCard()
        layout.addWidget(self.status)

        layout.addStretch()

    def update_source_info(self, file_path):
        try:
            import polars as pl
            if file_path.endswith('.csv'):
                df = pl.read_csv(file_path, has_header=True)
            else:
                df = pl.read_excel(file_path, engine='calamine')
            rows, cols = df.shape
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.source_rows_label.setText(f"{rows:,}")
            self.source_cols_label.setText(str(cols))
            self.source_size_label.setText(f"{size_mb:.1f} MB")
        except Exception:
            self.source_rows_label.setText("Error")
            self.source_cols_label.setText("Error")
            self.source_size_label.setText("Error")

    def update_target_info(self, file_path):
        try:
            import polars as pl
            df = pl.read_excel(file_path, engine='calamine')
            rows, cols = df.shape
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            self.target_rows_label.setText(f"{rows:,}")
            self.target_cols_label.setText(str(cols))
            self.target_size_label.setText(f"{size_mb:.1f} MB")
        except Exception:
            self.target_rows_label.setText("Error")
            self.target_cols_label.setText("Error")
            self.target_size_label.setText("Error")