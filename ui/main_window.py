import os
import sys
import subprocess
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ui.widgets.file_panel import FilePanel
from ui.widgets.sku_panel import SkuPanel
from ui.widgets.mapping_panel import MappingPanel
from ui.widgets.info_panel import InfoPanel
from ui.widgets.action_panel import ActionPanel
from ui.widgets.log_panel import LogPanel
from core.differ import Differ
from core.writer import Writer
from utils.report import ReportGenerator


class ExecuteWorker(QThread):
    progress_updated = Signal(str, int)
    step_completed = Signal(str, float)
    finished = Signal(dict)
    error = Signal(str)
    writer_progress = Signal(str)

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        t0 = time.time()
        try:
            self.progress_updated.emit("Reading...", 5)
            self.step_completed.emit("Source loaded", time.time() - t0)
            self.progress_updated.emit("Comparing...", 30)
            differ = Differ(self.data)
            diff = differ.compare()
            self.step_completed.emit("Comparison done", time.time() - t0)
            self.progress_updated.emit("Writing...", 60)
            writer = Writer(self.data, diff)
            writer.progress_updated.connect(self.writer_progress.emit)
            writer.write()
            self.step_completed.emit("File written", time.time() - t0)
            self.progress_updated.emit("Report...", 90)
            report = ReportGenerator.generate_report(diff, self.data)
            report['elapsed_time'] = time.time() - t0
            self.progress_updated.emit("Complete", 100)
            self.finished.emit(report)
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n{traceback.format_exc()}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session_data = {}
        self.worker = None
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle("MATTUpdater - Source to Target File Update Tool")
        self.setMinimumSize(1100, 750)
        self.resize(1250, 820)

        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("headerFrame")
        header.setFixedHeight(56)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 6, 14, 6)
        hl.setSpacing(10)
        logo = QLabel("M")
        logo.setFixedSize(38, 38)
        logo.setStyleSheet(
            "background-color: rgba(255,255,255,0.2); border-radius: 8px; "
            "font-size: 20px; color: white; font-weight: bold;"
        )
        logo.setAlignment(Qt.AlignCenter)
        hl.addWidget(logo)
        tw = QWidget()
        tl = QVBoxLayout(tw)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)
        tl.addWidget(QLabel("MATTUpdater", objectName="titleLabel"))
        tl.addWidget(QLabel("Source to Target File Update Tool", objectName="subtitleLabel"))
        hl.addWidget(tw)
        hl.addStretch()
        hl.addWidget(QLabel("v1.0.0", styleSheet="color: rgba(255,255,255,0.6); font-size: 10px;"))
        ml.addWidget(header)

        # Content
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        # LEFT PANEL
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.file_panel = FilePanel()
        self.sku_panel = SkuPanel()
        top_row.addWidget(self.file_panel, stretch=1)
        top_row.addWidget(self.sku_panel, stretch=1)
        left_layout.addLayout(top_row)

        self.mapping_panel = MappingPanel()
        left_layout.addWidget(self.mapping_panel)

        self.action_panel = ActionPanel()
        left_layout.addWidget(self.action_panel)

        splitter.addWidget(left)

        # RIGHT PANEL
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(6, 0, 0, 0)
        right_layout.setSpacing(10)

        self.info_panel = InfoPanel()
        right_layout.addWidget(self.info_panel)

        self.log_panel = LogPanel()
        right_layout.addWidget(self.log_panel, stretch=1)

        splitter.addWidget(right)
        splitter.setSizes([750, 450])

        cl.addWidget(splitter)
        ml.addWidget(content, stretch=1)

        # Status bar
        sb = QFrame()
        sb.setStyleSheet("QFrame { background-color: #2D1B3D; border-top: 1px solid #5A3D6B; }")
        sb.setFixedHeight(28)
        sl = QHBoxLayout(sb)
        sl.setContentsMargins(14, 2, 14, 2)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #FFFFFF; font-size: 10px;")
        sl.addWidget(self.status_label)
        sl.addStretch()
        ml.addWidget(sb)

    def connect_signals(self):
        self.file_panel.files_selected.connect(self.on_files_selected)
        self.sku_panel.sku_confirmed.connect(self.on_sku_confirmed)
        self.sku_panel.detection_warning.connect(self.log_panel.warning)
        self.action_panel.preview_clicked.connect(self.on_preview)
        self.action_panel.execute_clicked.connect(self.on_execute)

    def on_files_selected(self, sp, tp):
        self.status_label.setText("Loading...")
        QApplication.processEvents()
        self.info_panel.update_source_info(sp)
        self.info_panel.update_target_info(tp)
        self.sku_panel.detect_columns(sp, tp)
        self.log_panel.success("Files loaded")
        self.status_label.setText("Confirm SKU columns")

    def on_sku_confirmed(self, ssk, tsk):
        self.status_label.setText("Matching...")
        QApplication.processEvents()
        self.mapping_panel.perform_matching(
            self.file_panel.source_path,
            self.file_panel.target_path,
            ssk,
            tsk
        )
        self.log_panel.success(f"SKU: {ssk} -> {tsk}")
        self.status_label.setText("Ready")

    def on_preview(self):
        if not self._validate():
            return
        m = self.mapping_panel.get_confirmed_mapping()
        ssk, tsk = self.sku_panel.get_sku_columns()
        try:
            self.log_panel.clear()
            self.log_panel.info("Preview...")
            data = {
                'source_path': self.file_panel.source_path,
                'target_path': self.file_panel.target_path,
                'source_sku_col': ssk,
                'target_sku_col': tsk,
                'column_mapping': m,
                'output_path': self.file_panel.get_output_path()
            }
            diff = Differ(data).compare()
            self.log_panel.info(
                f"Updates: {len(diff.get('updates',[]))}, "
                f"New SKUs: {diff.get('new_skus',0)}, "
                f"New cols: {diff.get('new_columns_count',0)}"
            )
            for w in diff.get('warnings', []):
                self.log_panel.warning(w.get('message', str(w)))
        except Exception as e:
            self.log_panel.error(str(e))

    def on_execute(self):
        if not self._validate():
            return
        m = self.mapping_panel.get_confirmed_mapping()
        ssk, tsk = self.sku_panel.get_sku_columns()
        self.session_data = {
            'source_path': self.file_panel.source_path,
            'target_path': self.file_panel.target_path,
            'source_sku_col': ssk,
            'target_sku_col': tsk,
            'column_mapping': m,
            'output_path': self.file_panel.get_output_path()
        }
        self.log_panel.clear()
        self.log_panel.info("Starting...")
        self.action_panel.set_running(True)
        self.info_panel.status.set_running()
        self.worker = ExecuteWorker(self.session_data)
        self.worker.progress_updated.connect(self.action_panel.set_progress)
        self.worker.step_completed.connect(self.log_panel.step)
        self.worker.writer_progress.connect(self.log_panel.info)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_finished(self, report):
        self.action_panel.set_running(False)
        self.info_panel.status.set_done()
        e = report.get('elapsed_time', 0)
        m, s = int(e // 60), int(e % 60)
        self.log_panel.success(f"Done in {m}m{s}s")
        self.log_panel.info(
            f"Updated: {report.get('cells_updated',0)}, "
            f"New SKUs: {report.get('new_skus',0)}"
        )
        out = self.session_data.get('output_path', '')
        if QMessageBox.question(
            self, "Done", f"Open folder?\n{out}",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            folder = os.path.dirname(out)
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])

    def on_error(self, msg):
        self.action_panel.set_running(False)
        self.info_panel.status.set_error(msg[:100])
        self.log_panel.error(msg[:200])
        QMessageBox.critical(self, "Error", msg[:300])

    def _validate(self):
        if not self.file_panel.validate():
            QMessageBox.warning(self, "Error", "Select files.")
            return False
        if not self.sku_panel.validate():
            QMessageBox.warning(self, "Error", "Confirm SKU columns.")
            return False
        if not self.mapping_panel.validate():
            return False
        return True