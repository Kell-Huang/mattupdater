from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel
from PySide6.QtCore import Signal

class ActionPanel(QWidget):
    preview_clicked = Signal()
    execute_clicked = Signal()

    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); l.setSpacing(8)
        ar = QHBoxLayout(); ar.setSpacing(10)
        self.preview_btn = QPushButton("Preview Changes")
        self.preview_btn.clicked.connect(self.preview_clicked.emit)
        self.execute_btn = QPushButton("Execute Update")
        self.execute_btn.clicked.connect(self.execute_clicked.emit)
        ar.addWidget(self.preview_btn); ar.addWidget(self.execute_btn)
        pw = QWidget(); pl = QVBoxLayout(pw); pl.setContentsMargins(0,0,0,0); pl.setSpacing(2)
        self.progress_label = QLabel(""); self.progress_label.setStyleSheet("font-size:11px;color:#A08DB5;")
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0,100); self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True); self.progress_bar.setFormat("%p%")
        pl.addWidget(self.progress_label); pl.addWidget(self.progress_bar)
        ar.addWidget(pw,stretch=1)
        l.addLayout(ar)

    def set_progress(self, step, pct):
        self.progress_label.setText(step); self.progress_bar.setValue(pct)

    def set_running(self, running):
        self.preview_btn.setEnabled(not running); self.execute_btn.setEnabled(not running)
        if not running: self.progress_bar.setValue(0); self.progress_label.setText("")