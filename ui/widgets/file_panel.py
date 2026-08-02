import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLineEdit, QLabel, QFileDialog,
    QComboBox, QMessageBox
)
from PySide6.QtCore import Signal


class FilePanel(QGroupBox):
    files_selected = Signal(str, str)

    def __init__(self):
        super().__init__("File Selection")
        self.source_path = ""
        self.target_path = ""
        self._output_format = "xlsx"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Source file row
        src_layout = QHBoxLayout()
        src_label = QLabel("Source")
        src_label.setFixedWidth(55)
        src_label.setStyleSheet("font-weight: 600; color: #D4C4E0; font-size: 11px;")
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Select source...")
        self.source_input.setReadOnly(True)
        self.source_input.setFixedHeight(30)
        src_browse = QPushButton("Browse")
        src_browse.setFixedSize(65, 30)
        src_browse.setStyleSheet("font-size: 11px;")
        src_browse.clicked.connect(self.browse_source)
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.source_input, stretch=1)
        src_layout.addWidget(src_browse)
        layout.addLayout(src_layout)

        # Target file row
        tgt_layout = QHBoxLayout()
        tgt_label = QLabel("Target")
        tgt_label.setFixedWidth(55)
        tgt_label.setStyleSheet("font-weight: 600; color: #D4C4E0; font-size: 11px;")
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Select target...")
        self.target_input.setReadOnly(True)
        self.target_input.setFixedHeight(30)
        tgt_browse = QPushButton("Browse")
        tgt_browse.setFixedSize(65, 30)
        tgt_browse.setStyleSheet("font-size: 11px;")
        tgt_browse.clicked.connect(self.browse_target)
        tgt_layout.addWidget(tgt_label)
        tgt_layout.addWidget(self.target_input, stretch=1)
        tgt_layout.addWidget(tgt_browse)
        layout.addLayout(tgt_layout)

        # Output format row
        fmt_layout = QHBoxLayout()
        fmt_label = QLabel("Output")
        fmt_label.setFixedWidth(55)
        fmt_label.setStyleSheet("font-weight: 600; color: #D4C4E0; font-size: 11px;")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["XLSX (default)", "CSV (no formulas/format)"])
        self.format_combo.setFixedHeight(30)
        self.format_combo.setStyleSheet("""
            QComboBox {
                color: #F0EAF5;
                background-color: #3D2A50;
                border: 1px solid #5A3D6B;
                border-radius: 4px;
                padding: 0 8px;
            }
            QComboBox QAbstractItemView {
                color: #F0EAF5;
                background-color: #3D2A50;
                selection-background-color: #9B59B6;
                selection-color: white;
                border: 1px solid #5A3D6B;
                outline: none;
            }
        """)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        fmt_layout.addWidget(fmt_label)
        fmt_layout.addWidget(self.format_combo, stretch=1)
        layout.addLayout(fmt_layout)

    def _on_format_changed(self, index):
        if index == 1:
            QMessageBox.information(
                self,
                "CSV Output",
                "CSV format does NOT preserve:\n"
                "  - Excel formulas (will be saved as values)\n"
                "  - Cell formatting (colors, fonts, borders)\n"
                "  - Column widths\n\n"
                "Use CSV only if you need fast processing and don't require formatting.",
            )

    def browse_source(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Source File", "",
            "Excel/CSV Files (*.xlsx *.xls *.csv);;All Files (*.*)"
        )
        if file_path:
            self.source_path = file_path
            self.source_input.setText(file_path)
            self._notify_if_ready()

    def browse_target(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Target File", "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        if file_path:
            self.target_path = file_path
            self.target_input.setText(file_path)
            self._notify_if_ready()

    def _notify_if_ready(self):
        if self.source_path and self.target_path:
            self.files_selected.emit(self.source_path, self.target_path)

    def get_output_path(self):
        if not self.target_path:
            return ""
        d = os.path.dirname(self.target_path)
        base = os.path.splitext(os.path.basename(self.target_path))[0]
        if self.format_combo.currentIndex() == 1:
            return os.path.join(d, f"{base}_updated.csv")
        return os.path.join(d, f"{base}_updated.xlsx")

    def get_output_format(self):
        return "csv" if self.format_combo.currentIndex() == 1 else "xlsx"

    def validate(self):
        return bool(self.source_path and self.target_path)