import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ui.main_window import MainWindow


def get_dark_purple_theme():
    """Return the dark purple theme stylesheet."""
    return """
    QMainWindow { background: #2D1B3D; }
    QWidget { color: #F0EAF5; font-size: 13px; }
    QMessageBox { color: #000000; background: #FFFFFF; }
    QMessageBox QLabel { color: #000000; }

    QTableWidget {
        background: #3D2A50; border: 1px solid #5A3D6B; border-radius: 4px;
        gridline-color: #3D2A50;
    }
    QTableWidget::item { background: #3D2A50; color: #F0EAF5; }
    QTableCornerButton::section { background: #9B59B6; border: none; }

    QHeaderView::section {
        background: #9B59B6; color: white; padding: 6px; border: none;
        font-weight: bold; font-size: 11px;
    }
    QHeaderView::section:vertical {
        background: #9B59B6; color: white; border: none;
        font-size: 11px; padding: 4px 6px;
    }

    QPushButton {
        background: #9B59B6; color: white; border: none; border-radius: 4px;
        font-weight: 600; font-size: 12px; padding: 4px 14px;
    }
    QPushButton:hover { background: #8E44AD; }

    QPushButton#successBtn {
        background-color: #27AE60; color: white; border-radius: 4px;
        font-size: 11px; font-weight: bold;
    }
    QPushButton#successBtn:hover { background-color: #219A52; }

    QPushButton#dangerBtn {
        background-color: #E74C3C; color: white; border-radius: 4px;
        font-size: 11px; font-weight: bold;
    }
    QPushButton#dangerBtn:hover { background-color: #C0392B; }

    QLineEdit {
        background: transparent; border: none; border-radius: 0px;
        padding: 0px 8px; color: #F0EAF5; font-size: 12px;
    }

    /* Combo box dropdown list - black text on white background */
    QComboBox {
        background: #3D2A50; border: 1px solid #5A3D6B; border-radius: 4px;
        padding: 4px 8px; color: #F0EAF5; font-size: 12px;
    }
    QComboBox QAbstractItemView {
        background: #FFFFFF; color: #000000;
        border: 1px solid #5A3D6B; border-radius: 4px;
        selection-background-color: #9B59B6; selection-color: white;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 4px 8px; min-height: 24px; color: #000000;
    }

    QListWidget {
        background: #FFFFFF; color: #000000;
        border: 1px solid #5A3D6B; border-radius: 4px;
        selection-background-color: #9B59B6; selection-color: white;
        outline: none;
    }
    QListWidget::item { padding: 4px 8px; min-height: 24px; color: #000000; }

    QCheckBox::indicator {
        width: 13px; height: 13px; border: 2px solid #9B59B6; border-radius: 2px;
        background: #2D1B3D;
    }
    QCheckBox::indicator:checked {
        background: #27AE60; border-color: #27AE60;
    }

    QFrame#headerFrame { background-color: #6C3483; }
    QFrame#infoCard {
        background-color: #3D2A50; border: 1px solid #5A3D6B; border-radius: 6px;
    }
    QWidget#logPanel {
        background-color: #2D1B3D; border: 1px solid #5A3D6B; border-radius: 6px;
    }
    """


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MATTUpdater")
    app.setOrganizationName("MATTUpdater")
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    app.setStyleSheet(get_dark_purple_theme())
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()