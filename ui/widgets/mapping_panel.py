# ============================================================
# File: mattupdater/ui/widgets/mapping_panel.py
# ============================================================
"""
Column mapping panel with searchable target columns.
Supports Shift+Click range selection on Source Column.
Add/Del buttons auto-toggle checkbox selection.
Fixed: use clicked signal instead of stateChanged for reliable toggle.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QApplication, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt, QEvent
from PySide6.QtGui import QFont, QColor
from functools import partial

from core.column_matcher import ColumnMatcher


class FloatingDropdown(QListWidget):
    """Floating dropdown list for column search."""
    item_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMinimumHeight(100)
        self.setMaximumHeight(180)
        self.setStyleSheet(
            "QListWidget { background: #FFFFFF; color: #000000; "
            "border: 1px solid #5A3D6B; border-radius: 4px; }"
            "QListWidget::item { color: #000000; padding: 4px 8px; min-height: 24px; }"
        )
        self.itemClicked.connect(self._on_item_clicked)
        self.hide()

    def set_items(self, items):
        self.clear()
        for text in items:
            item = QListWidgetItem(text)
            item.setForeground(QColor("#000000"))
            item.setFont(QFont("Segoe UI", 10))
            self.addItem(item)

    def filter_items(self, text):
        for i in range(self.count()):
            item = self.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def show_at(self, global_pos, width):
        self.setFixedWidth(width)
        if self.parent() is None:
            self.move(global_pos)
        else:
            parent_pos = self.parent().mapFromGlobal(global_pos)
            self.move(parent_pos)
        self.show()
        self.raise_()

    def _on_item_clicked(self, item):
        self.item_selected.emit(item.text())
        self.hide()


class SearchableCell(QWidget):
    """Unified cell widget for all Target Column types."""
    selection_made = Signal(str)

    def __init__(self, all_items, initial_text="", editable=True, parent=None):
        super().__init__(parent)
        self.all_items = all_items

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.edit = QLineEdit()
        self.edit.setFont(QFont("Segoe UI", 9))
        self.edit.setFixedHeight(30)
        self.edit.setText(initial_text)
        self.edit.setReadOnly(not editable)
        if editable:
            self.edit.setPlaceholderText("Type to search...")
            self.edit.textChanged.connect(self._on_text_changed)
            self.edit.installEventFilter(self)
        layout.addWidget(self.edit)

        self._dropdown = None

    def _get_dropdown(self):
        if self._dropdown is None:
            self._dropdown = FloatingDropdown(None)
            self._dropdown.set_items(self.all_items)
            self._dropdown.item_selected.connect(self._on_item_selected)
        return self._dropdown

    def _on_text_changed(self, text):
        dropdown = self._get_dropdown()
        if not text.strip():
            dropdown.hide()
            return
        dropdown.filter_items(text)
        global_pos = self.edit.mapToGlobal(self.edit.rect().bottomLeft())
        dropdown.show_at(global_pos, self.edit.width())

    def _on_item_selected(self, text):
        self.edit.blockSignals(True)
        self.edit.setText(text)
        self.edit.blockSignals(False)
        if self._dropdown:
            self._dropdown.hide()
        self.selection_made.emit(text)
        self.edit.setFocus()

    def eventFilter(self, obj, event):
        if obj == self.edit:
            if event.type() == QEvent.FocusOut:
                if self._dropdown and self._dropdown.isVisible():
                    self._dropdown.hide()
            elif event.type() == QEvent.KeyPress:
                key_event = event
                dropdown = self._get_dropdown() if self._dropdown else None
                if key_event.key() == Qt.Key_Escape:
                    if dropdown: dropdown.hide()
                    return True
                if key_event.key() == Qt.Key_Down and dropdown and dropdown.isVisible():
                    if dropdown.count() > 0:
                        dropdown.setCurrentRow(0)
                    return True
                if key_event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    if dropdown and dropdown.isVisible() and dropdown.currentItem():
                        self._on_item_selected(dropdown.currentItem().text())
                        return True
        return super().eventFilter(obj, event)

    def get_selected_text(self):
        return self.edit.text().strip()


class MappingPanel(QGroupBox):
    """Column mapping panel with searchable target columns and batch selection."""
    mapping_confirmed = Signal(dict)

    def __init__(self):
        super().__init__("Column Mapping")
        self.column_matcher = ColumnMatcher()
        self.mapping_results = []
        self.prefix_info = {}
        self.new_columns = {}
        self.target_columns = []
        self.last_checked_row = -1
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        hdr = QHBoxLayout()
        self.summary_label = QLabel("Matched: 0/0  |  Selected: 0  |  New: 0  |  Unmatched: 0")
        self.summary_label.setStyleSheet("font-size: 11px; color: #A08DB5;")
        hdr.addWidget(self.summary_label)
        hdr.addStretch()
        main_layout.addLayout(hdr)

        self.prefix_label = QLabel()
        self.prefix_label.setStyleSheet(
            "font-size: 10px; color: #D4C4E0; padding: 4px 8px; "
            "background-color: #2D1B3D; border-radius: 4px;"
        )
        self.prefix_label.hide()
        main_layout.addWidget(self.prefix_label)

        al = QHBoxLayout()
        al.setSpacing(6)

        self.select_all_btn = QPushButton("Deselect All")
        self.select_all_btn.setFixedHeight(26)
        self.select_all_btn.clicked.connect(self.toggle_select_all)

        btn_dir = QPushButton("Direct Only")
        btn_dir.setFixedHeight(26); btn_dir.clicked.connect(lambda: self.filter_by_type("direct"))
        btn_unm = QPushButton("Unmatched Only")
        btn_unm.setFixedHeight(26); btn_unm.clicked.connect(lambda: self.filter_by_type("none"))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search..."); self.search.setFixedHeight(26); self.search.setFixedWidth(130)
        self.search.textChanged.connect(self.filter_table)

        al.addWidget(self.select_all_btn); al.addWidget(btn_dir); al.addWidget(btn_unm)
        al.addStretch(); al.addWidget(self.search)
        main_layout.addLayout(al)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Sel/Type", "Source Column", "", "Target Column", "Act"])
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        vh = self.table.verticalHeader()
        vh.setStyleSheet("background-color: #9B59B6; color: white;")
        vh.setDefaultAlignment(Qt.AlignCenter)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 95)
        self.table.setColumnWidth(2, 22)
        self.table.setColumnWidth(4, 55)
        self.table.setMaximumHeight(350)
        main_layout.addWidget(self.table)

    def perform_matching(self, sp, tp, ssk, tsk):
        try:
            import polars as pl
            if sp.endswith('.csv'):
                sdf = pl.read_csv(sp, has_header=True)
            else:
                sdf = pl.read_excel(sp, engine='calamine')
            tdf = pl.read_excel(tp, engine='calamine')
            src_cols = [c for c in sdf.columns if c != ssk]
            self.target_columns = tdf.columns
            self.mapping_results, self.prefix_info = self.column_matcher.match_columns(src_cols, self.target_columns)
            pref = self.prefix_info.get('most_common_prefix', '')
            self.prefix_label.setText(
                f"Detected prefix: '{pref}' - New columns: {pref}[source]" if pref
                else "No common prefix. New columns will use source names directly."
            )
            self.prefix_label.show()
            self.new_columns = {}
            self.last_checked_row = -1
            for r in self.mapping_results:
                r['selected'] = True
            self.populate_table()
            self.update_summary()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Matching failed: {e}")

    def populate_table(self):
        self.table.setRowCount(len(self.mapping_results))
        font = QFont("Segoe UI", 9)
        all_targets = self.target_columns

        for row, res in enumerate(self.mapping_results):
            cw = QWidget()
            chl = QHBoxLayout(cw)
            chl.setContentsMargins(4, 0, 2, 0)
            chl.setSpacing(4)
            chl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            cb = QCheckBox()
            cb.setFocusPolicy(Qt.StrongFocus)
            # Use clicked signal instead of stateChanged
            cb.clicked.connect(partial(self._on_checkbox_clicked, row))
            cb.setChecked(res.get('selected', False))

            txt, bg_color = self._type_info(res)
            badge = QLabel(txt)
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedSize(68, 18)
            badge.setStyleSheet(
                f"background-color: {bg_color}; color: white; "
                f"border-radius: 3px; font-size: 9px; font-weight: bold;"
            )
            chl.addWidget(cb)
            chl.addWidget(badge)
            self.table.setCellWidget(row, 0, cw)

            si = QTableWidgetItem(res['source'])
            si.setFont(font)
            si.setFlags(si.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, si)

            ai = QTableWidgetItem("→")
            ai.setTextAlignment(Qt.AlignCenter)
            ai.setForeground(QColor("#FFFFFF"))
            self.table.setItem(row, 2, ai)

            is_unmatched = (res['match_type'] == 'none' and res['source'] not in self.new_columns)
            is_indirect = (res['match_type'] == 'indirect')
            is_new = (res['source'] in self.new_columns)

            if is_new:
                search_cell = SearchableCell(all_targets, self.new_columns[res['source']], editable=False)
                self.table.setCellWidget(row, 3, search_cell)
            elif is_unmatched or is_indirect:
                initial = res['target'] if is_indirect and res['target'] else ""
                search_cell = SearchableCell(all_targets, initial, editable=True)
                search_cell.selection_made.connect(lambda text, r=row: self._on_search_select(r, text))
                self.table.setCellWidget(row, 3, search_cell)
            else:
                search_cell = SearchableCell(all_targets, res['target'] or "", editable=False)
                self.table.setCellWidget(row, 3, search_cell)

            self._set_action_cell(row, res)

            if bg_color == "#F39C12":
                bg = "#3D2A40"
            elif bg_color == "#E74C3C":
                bg = "#3D2A2A"
            elif bg_color == "#17A2B8":
                bg = "#2D3D30"
            else:
                bg = None
            if bg:
                for c in range(5):
                    item = self.table.item(row, c)
                    if item:
                        item.setBackground(QColor(bg))

    def _type_info(self, res):
        if res['match_type'] == 'direct':
            return ("DIRECT", "#27AE60")
        elif res['match_type'] == 'indirect':
            return ("INDIRECT", "#F39C12")
        else:
            if res['source'] in self.new_columns:
                return ("NEW", "#17A2B8")
            else:
                return ("UNMATCHED", "#E74C3C")

    def _set_action_cell(self, row, res):
        if res['match_type'] == 'none' and res['source'] not in self.new_columns:
            btn = QPushButton("Add")
            btn.setObjectName("successBtn")
            btn.setFixedSize(50, 24)
            btn.clicked.connect(lambda checked, r=row: self.add_single_new_column(r))
            self.table.setCellWidget(row, 4, btn)
        elif res['source'] in self.new_columns:
            btn = QPushButton("Del")
            btn.setObjectName("dangerBtn")
            btn.setFixedSize(50, 24)
            btn.clicked.connect(lambda checked, r=row: self.remove_new_column(r))
            self.table.setCellWidget(row, 4, btn)
        else:
            self.table.setItem(row, 4, QTableWidgetItem(""))

    def _on_search_select(self, row, text):
        if row < len(self.mapping_results):
            self.mapping_results[row]['target'] = text

    def _get_checkbox(self, row):
        cw = self.table.cellWidget(row, 0)
        if cw:
            return cw.findChild(QCheckBox)
        return None

    def _sync_all_checkboxes(self):
        for row in range(self.table.rowCount()):
            cb = self._get_checkbox(row)
            if cb:
                cb.blockSignals(True)
                cb.setChecked(self.mapping_results[row].get('selected', False))
                cb.blockSignals(False)

    def _on_checkbox_clicked(self, row):
        """Handle checkbox click with Shift support."""
        shift_held = QApplication.keyboardModifiers() == Qt.ShiftModifier
        if shift_held and self.last_checked_row >= 0:
            start = min(self.last_checked_row, row)
            end = max(self.last_checked_row, row)
            for r in range(start, end + 1):
                self.mapping_results[r]['selected'] = True
            self._sync_all_checkboxes()
        else:
            new_state = not self.mapping_results[row].get('selected', False)
            self.mapping_results[row]['selected'] = new_state
            cb = self._get_checkbox(row)
            if cb:
                cb.setChecked(new_state)

        self.last_checked_row = row
        self.update_summary()
        self._update_select_all_btn()

    def add_single_new_column(self, row):
        src = self.mapping_results[row]['source']
        pref = self.prefix_info.get('most_common_prefix', '')
        new_name = self.column_matcher.generate_new_column_name(src, pref, self.target_columns)
        if new_name is None:
            QMessageBox.warning(self, "Conflict", f"Column '{pref}{src}' already exists.")
            return
        self.new_columns[src] = new_name
        self.mapping_results[row]['target'] = new_name
        self.mapping_results[row]['selected'] = True
        self.refresh_table()
        self.update_summary()

    def remove_new_column(self, row):
        src = self.mapping_results[row]['source']
        if src in self.new_columns:
            del self.new_columns[src]
            self.mapping_results[row]['target'] = None
            self.mapping_results[row]['selected'] = False
        self.refresh_table()
        self.update_summary()

    def refresh_table(self):
        self.table.setRowCount(0)
        self.populate_table()

    def toggle_select_all(self):
        if all(r.get('selected', False) for r in self.mapping_results):
            self.deselect_all()
        else:
            self.select_all()

    def select_all(self):
        for r in self.mapping_results:
            r['selected'] = True
        self.refresh_table()
        self.update_summary()
        self._update_select_all_btn()

    def deselect_all(self):
        for r in self.mapping_results:
            r['selected'] = False
        self.refresh_table()
        self.update_summary()
        self._update_select_all_btn()

    def filter_by_type(self, mt):
        for r in self.mapping_results:
            r['selected'] = (r['match_type'] == mt)
        self.refresh_table()
        self.update_summary()
        self._update_select_all_btn()

    def _update_select_all_btn(self):
        if all(r.get('selected', False) for r in self.mapping_results):
            self.select_all_btn.setText("Deselect All")
        else:
            self.select_all_btn.setText("Select All")

    def filter_table(self, text):
        t = text.lower()
        for row in range(self.table.rowCount()):
            src = self.table.item(row, 1).text().lower()
            tw = self.table.cellWidget(row, 3)
            if isinstance(tw, SearchableCell):
                tgt = tw.get_selected_text().lower()
            elif self.table.item(row, 3):
                tgt = self.table.item(row, 3).text().lower()
            else:
                tgt = ""
            self.table.setRowHidden(row, not (t in src or t in tgt))

    def update_summary(self):
        total = len(self.mapping_results)
        mat = sum(1 for r in self.mapping_results if r['match_type'] != 'none')
        sel = sum(1 for r in self.mapping_results if r.get('selected') is True)
        unm = total - mat
        new = len(self.new_columns)
        self.summary_label.setText(f"Matched: {mat}/{total}  |  Selected: {sel}  |  New: {new}  |  Unmatched: {unm}")

    def get_confirmed_mapping(self):
        m = {'updates': {}, 'new_columns': {}, 'prefix': self.prefix_info.get('most_common_prefix', '')}
        for r in self.mapping_results:
            if r.get('selected'):
                s, t = r['source'], r['target']
                if s in self.new_columns and t:
                    m['new_columns'][s] = t
                elif r['match_type'] != 'none' and t:
                    m['updates'][s] = t
        return m

    def validate(self):
        us = [r['source'] for r in self.mapping_results if r['match_type'] == 'none' and r.get('selected') and r['source'] not in self.new_columns]
        if us:
            if QMessageBox.warning(self, "Unmatched", f"Selected but unmatched: {', '.join(us)}\nContinue?", QMessageBox.Ok | QMessageBox.Ignore, QMessageBox.Ok) == QMessageBox.Ok:
                return False
        if sum(1 for r in self.mapping_results if r.get('selected')) == 0:
            QMessageBox.warning(self, "None", "Select at least one column.")
            return False
        self.mapping_confirmed.emit(self.get_confirmed_mapping())
        return True