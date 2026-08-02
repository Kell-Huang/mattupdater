from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QLabel, QCompleter
)
from PySide6.QtCore import Signal, Qt, QStringListModel
from PySide6.QtGui import QFont


from core.sku_detector import SkuDetector


class SkuPanel(QGroupBox):
    sku_confirmed = Signal(str, str)
    detection_warning = Signal(str)

    def __init__(self):
        super().__init__("SKU Columns")
        self.sku_detector = SkuDetector()
        self.source_sku_col = ""
        self.target_sku_col = ""
        self._source_items = []
        self._target_items = []
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        combo_box_style = """
            QComboBox {
                color: #F0EAF5;
                background-color: #3D2A50;
                border: 1px solid #5A3D6B;
                border-radius: 4px;
                padding: 0 8px;
            }
        """

        src_layout = QVBoxLayout()
        self.src_conf = QLabel("Waiting for files...")
        self.src_conf.setStyleSheet("font-size: 10px; color: #A08DB5;")
        self.src_combo = QComboBox()
        self.src_combo.setEditable(True)
        self.src_combo.setInsertPolicy(QComboBox.NoInsert)
        self.src_combo.setFont(QFont("Segoe UI", 9))
        self.src_combo.setFixedHeight(30)
        self.src_combo.setStyleSheet(combo_box_style)
        self.src_combo.setMaxVisibleItems(0)
        self.src_combo.activated.connect(self._on_source_activated)
        src_layout.addWidget(self.src_conf)
        src_layout.addWidget(self.src_combo)
        layout.addLayout(src_layout)

        tgt_layout = QVBoxLayout()
        self.tgt_conf = QLabel("Waiting for files...")
        self.tgt_conf.setStyleSheet("font-size: 10px; color: #A08DB5;")
        self.tgt_combo = QComboBox()
        self.tgt_combo.setEditable(True)
        self.tgt_combo.setInsertPolicy(QComboBox.NoInsert)
        self.tgt_combo.setFont(QFont("Segoe UI", 9))
        self.tgt_combo.setFixedHeight(30)
        self.tgt_combo.setStyleSheet(combo_box_style)
        self.tgt_combo.setMaxVisibleItems(0)
        self.tgt_combo.activated.connect(self._on_target_activated)
        tgt_layout.addWidget(self.tgt_conf)
        tgt_layout.addWidget(self.tgt_combo)
        layout.addLayout(tgt_layout)

    def detect_columns(self, source_path, target_path):
        try:
            import polars as pl
            if source_path.endswith('.csv'):
                src_df = pl.read_csv(source_path, has_header=True)
            else:
                src_df = pl.read_excel(source_path, engine='calamine')
            src_cols = src_df.columns
            self._source_items = list(src_cols)
            src_res = self.sku_detector.detect_sku_column(src_cols)

            self._setup_combo(self.src_combo, src_cols, src_res)
            if src_res:
                self.src_combo.setCurrentText(src_res[0])
                self.source_sku_col = src_res[0]
                self.src_conf.setText("● Detected")
                self.src_conf.setStyleSheet("font-size: 10px; color: #27AE60;")
            else:
                self.src_conf.setText("⚠ Not detected")
                self.src_conf.setStyleSheet("font-size: 10px; color: #F39C12;")
                self.detection_warning.emit("Source SKU column not detected. Please select manually.")

            tgt_df = pl.read_excel(target_path, engine='calamine')
            tgt_cols = tgt_df.columns
            self._target_items = list(tgt_cols)
            tgt_res = self.sku_detector.detect_sku_column(tgt_cols)

            self._setup_combo(self.tgt_combo, tgt_cols, tgt_res)
            if tgt_res:
                self.tgt_combo.setCurrentText(tgt_res[0])
                self.target_sku_col = tgt_res[0]
                self.tgt_conf.setText("● Detected")
                self.tgt_conf.setStyleSheet("font-size: 10px; color: #27AE60;")
            else:
                self.tgt_conf.setText("⚠ Not detected")
                self.tgt_conf.setStyleSheet("font-size: 10px; color: #F39C12;")
                self.detection_warning.emit("Target SKU column not detected. Please select manually.")

            if self.source_sku_col and self.target_sku_col:
                self.sku_confirmed.emit(self.source_sku_col, self.target_sku_col)
        except Exception as e:
            self.src_conf.setText("⚠ Error")
            self.src_conf.setStyleSheet("font-size: 10px; color: #E74C3C;")
            self.detection_warning.emit(f"SKU detection error: {e}")

    def _setup_combo(self, combo, items, detected_list):
        """Configure editable combo with completer for search filtering."""
        combo.clear()
        combo.addItems(items)

        completer = QCompleter(items)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)

        popup = completer.popup()
        popup.setFont(QFont("Segoe UI", 9))
        popup.setStyleSheet("""
            QListView {
                background-color: #3D2A50;
                color: #F0EAF5;
                font-size: 10px;
                border: 1px solid #5A3D6B;
                selection-background-color: #9B59B6;
                selection-color: white;
                padding: 0px;
            }
        """)

        combo.setCompleter(completer)

    def _is_valid_column(self, text, items):
        """Check if the entered text is a valid column name in the file."""
        return text in items

    def _on_source_activated(self, index):
        """Called when user selects an item from the dropdown or presses Enter."""
        text = self.src_combo.currentText().strip()
        if self._is_valid_column(text, self._source_items):
            self.source_sku_col = text
            if self.source_sku_col and self.target_sku_col:
                self.sku_confirmed.emit(self.source_sku_col, self.target_sku_col)
        else:
            self.detection_warning.emit(f"Source SKU column '{text}' not found in file.")

    def _on_target_activated(self, index):
        """Called when user selects an item from the dropdown or presses Enter."""
        text = self.tgt_combo.currentText().strip()
        if self._is_valid_column(text, self._target_items):
            self.target_sku_col = text
            if self.source_sku_col and self.target_sku_col:
                self.sku_confirmed.emit(self.source_sku_col, self.target_sku_col)
        else:
            self.detection_warning.emit(f"Target SKU column '{text}' not found in file.")

    def get_sku_columns(self):
        return self.src_combo.currentText(), self.tgt_combo.currentText()

    def validate(self):
        s = self.src_combo.currentText()
        t = self.tgt_combo.currentText()
        if s and t:
            if self._is_valid_column(s, self._source_items) and self._is_valid_column(t, self._target_items):
                self.source_sku_col = s
                self.target_sku_col = t
                return True
        return False