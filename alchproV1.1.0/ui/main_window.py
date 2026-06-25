# alchPRO/ui/main_window.py
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, 
                             QComboBox, QPushButton, QLabel, QSplitter, 
                             QMessageBox, QDialog, QFormLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QAction

from config import OSRS_STYLESHEET, MAGIC_XP_PER_CAST
from services.api import WikiAPI
from services.calculator import AlchCalculator
from repositories.file_handler import FileHandler

"""
Project: OSRS Live High Alch Profit Tracker
Author: pooping Pine pricklies
File: main_window.py
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSRS Live High Alch Profit Tracker")
        self.setGeometry(100, 100, 1200, 700)

        # Application State
        self.profiles = []
        self.history_logs = []
        self.calculated_items_cache = []
        self.mapping_data = []
        self.prices_data = {}
        self.volume_data = {}
        self._loading_history = False

        self.init_ui()
        self.load_data_on_boot()

        self.sync_live_wiki_data()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_live_wiki_data)
        self.timer.start(60000)

    def load_data_on_boot(self):
        self.profiles = FileHandler.load_profiles()
        self.history_logs = FileHandler.load_history(self.profiles)
        self.update_profile_dropdowns()
        self.render_history_table_view()
        self.recalculate_global_aggregates()

    def init_ui(self):
        self.setStyleSheet(OSRS_STYLESHEET)
        main_central = QWidget()
        self.setCentralWidget(main_central)
        outer_layout = QVBoxLayout(main_central)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(10)

        workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        outer_layout.addWidget(workspace_splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.right_workspace_panel = QWidget()
        right_layout = QVBoxLayout(self.right_workspace_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        workspace_splitter.addWidget(left_panel)
        workspace_splitter.addWidget(self.right_workspace_panel)
        workspace_splitter.setSizes([750, 550])

        # Left Top Bar
        top_bar = QHBoxLayout()
        left_layout.addLayout(top_bar)
        
        top_bar.addWidget(QLabel("Search:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter item name...")
        self.txt_search.textChanged.connect(self.apply_ui_table_filters)
        top_bar.addWidget(self.txt_search)

        top_bar.addWidget(QLabel("Nature Rune GP:"))
        self.txt_nat_rune = QLineEdit("90")
        self.txt_nat_rune.setFixedWidth(70)
        self.txt_nat_rune.textChanged.connect(self.trigger_recalculation)
        top_bar.addWidget(self.txt_nat_rune)

        self.btn_manual_sync = QPushButton("Sync Live Wiki Data")
        self.btn_manual_sync.clicked.connect(self.sync_live_wiki_data)
        top_bar.addWidget(self.btn_manual_sync)
        
        self.btn_toggle_logs = QPushButton("Minimize Logs")
        self.btn_toggle_logs.clicked.connect(self.toggle_logs_panel)
        top_bar.addWidget(self.btn_toggle_logs)

        # Checkboxes
        chk_row = QHBoxLayout()
        left_layout.addLayout(chk_row)
        
        self.chk_hide_losses = QCheckBox("Hide Losses")
        self.chk_hide_losses.toggled.connect(self.apply_ui_table_filters)
        chk_row.addWidget(self.chk_hide_losses)

        self.chk_hide_low_vol = QCheckBox("Hide Low Vol (<50/hr)")
        self.chk_hide_low_vol.setChecked(True)
        self.chk_hide_low_vol.toggled.connect(self.apply_ui_table_filters)
        chk_row.addWidget(self.chk_hide_low_vol)

        self.chk_inc_members = QCheckBox("Include Members Items")
        self.chk_inc_members.toggled.connect(self.apply_ui_table_filters)
        chk_row.addWidget(self.chk_inc_members)
        chk_row.addStretch()

        # Items Table
        self.tbl_items = QTableWidget(0, 9)
        self.tbl_items.setHorizontalHeaderLabels([
            "Item Name", "Sell Price", "Buy Price", "Best Cost", 
            "Alch Value", "Nat Cost", "Net Profit", "1h Volume", "GE Limit"
        ])
        widths = [130, 70, 70, 70, 75, 60, 85, 75, 70]
        for i, w in enumerate(widths): self.tbl_items.setColumnWidth(i, w)
        self.tbl_items.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_items.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl_items.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_items.cellDoubleClicked.connect(self.open_logging_dialog)
        left_layout.addWidget(self.tbl_items)

        # Right Panel Config
        prof_row = QHBoxLayout()
        right_layout.addLayout(prof_row)
        prof_row.addWidget(QLabel("Profile Filter:"))
        self.cmb_profile_filter = QComboBox()
        self.cmb_profile_filter.currentTextChanged.connect(self.handle_profile_filter_changed)
        prof_row.addWidget(self.cmb_profile_filter)
        
        btn_add = QPushButton("+ Add Profile")
        btn_add.clicked.connect(self.prompt_add_profile)
        prof_row.addWidget(btn_add)
        
        btn_del = QPushButton("- Del Profile")
        btn_del.clicked.connect(self.delete_active_profile)
        prof_row.addWidget(btn_del)
        prof_row.addStretch()

        # History Table
        self.tbl_history = QTableWidget(0, 5)
        self.tbl_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_history.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl_history.cellChanged.connect(self.handle_log_edit)
        right_layout.addWidget(self.tbl_history)

        # Log Utils
        util_row = QHBoxLayout()
        btn_dupe = QPushButton("Dupe Row")
        btn_dupe.clicked.connect(self.duplicate_selected_history_row)
        util_row.addWidget(btn_dupe)
        
        btn_del_row = QPushButton("Delete Row")
        btn_del_row.setStyleSheet("background-color: #5c1d1d; color: #ff9999; border: 1px solid #8f2d2d;") 
        btn_del_row.clicked.connect(self.delete_selected_history_row)
        util_row.addWidget(btn_del_row)
        
        btn_fix = QPushButton("Fix Old Math")
        btn_fix.setStyleSheet("color: #ffb74d; border: 1px dashed #ff9800;")
        btn_fix.clicked.connect(self.trigger_fix_math)
        util_row.addWidget(btn_fix)
        util_row.addStretch()
        right_layout.addLayout(util_row)

        # Bottom Toolbar
        bottom_bar = QHBoxLayout()
        outer_layout.addLayout(bottom_bar)
        
        bottom_bar.addWidget(QLabel("Casts Logged:"))
        self.txt_total_casts = QLineEdit("0")
        self.txt_total_casts.textChanged.connect(self.handle_manual_override)
        bottom_bar.addWidget(self.txt_total_casts)

        bottom_bar.addWidget(QLabel("Total Profit (GP):"))
        self.txt_total_profit = QLineEdit("0")
        self.txt_total_profit.textChanged.connect(self.handle_manual_override)
        bottom_bar.addWidget(self.txt_total_profit)

        bottom_bar.addWidget(QLabel("Magic XP Gained:"))
        self.txt_total_xp = QLineEdit("0")
        self.txt_total_xp.textChanged.connect(self.handle_manual_override)
        bottom_bar.addWidget(self.txt_total_xp)
        bottom_bar.addStretch()
        
        btn_reset = QPushButton("Reset Tracker & Logs")
        btn_reset.setStyleSheet("background-color: #5c1d1d; color: #ff9999; border: 1px solid #8f2d2d;")
        btn_reset.clicked.connect(self.reset_tracker)
        bottom_bar.addWidget(btn_reset)
        

        footer_label = QLabel("© 2026 AeRoLogic | OSRS Live High Alch Profit Tracker")
        footer_label.setStyleSheet("color: #888888; font-size: 10px;")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer_label.setFixedHeight(20)  # Force the label to stay thin
        outer_layout.addWidget(footer_label) # Add directly to outer_layout

    def toggle_logs_panel(self):
        visible = not self.right_workspace_panel.isVisible()
        self.right_workspace_panel.setVisible(visible)
        self.btn_toggle_logs.setText("Minimize Logs" if visible else "Show Logs")

    def sync_live_wiki_data(self):
        success, map_d, price_d, vol_d, nat_cost = WikiAPI.fetch_all_data()
        if success:
            self.mapping_data = map_d
            self.prices_data = price_d
            self.volume_data = vol_d
            self.txt_nat_rune.setText(str(nat_cost))
            self.trigger_recalculation()
        else:
            print(f"API Sync failed: {map_d}")

    def trigger_recalculation(self):
        try:
            nat_cost = int(self.txt_nat_rune.text().replace(',', '').strip())
        except ValueError:
            nat_cost = 0
            
        self.calculated_items_cache = AlchCalculator.process_items(
            self.mapping_data, self.prices_data, self.volume_data, nat_cost
        )
        self.apply_ui_table_filters()

    def apply_ui_table_filters(self):
        search_term = self.txt_search.text().strip().lower()
        hide_losses = self.chk_hide_losses.isChecked()
        hide_low_vol = self.chk_hide_low_vol.isChecked()
        inc_members = self.chk_inc_members.isChecked()

        self.tbl_items.setRowCount(0)
        self.tbl_items.setSortingEnabled(False)

        for item in self.calculated_items_cache:
            if search_term and search_term not in item['name'].lower(): continue
            if hide_losses and item['net_profit'] <= 0: continue
            if hide_low_vol and item['volume'] < 50: continue
            if not inc_members and item['members']: continue

            row_idx = self.tbl_items.rowCount()
            self.tbl_items.insertRow(row_idx)

            name_item = QTableWidgetItem(item['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, item['id'])
            
            p_item = QTableWidgetItem(f"{item['net_profit']:,}")
            p_item.setForeground(QColor('#00aa00' if item['net_profit'] > 0 else '#ff0000'))
            
            vol_item = QTableWidgetItem(f"{item['volume']:,}")
            if item['volume'] < 50: vol_item.setForeground(QColor('#ff7f00'))

            self.tbl_items.setItem(row_idx, 0, name_item)
            self.tbl_items.setItem(row_idx, 1, QTableWidgetItem(f"{item['high_price']:,}"))
            self.tbl_items.setItem(row_idx, 2, QTableWidgetItem(f"{item['low_price']:,}"))
            self.tbl_items.setItem(row_idx, 3, QTableWidgetItem(f"{item['best_cost']:,}"))
            self.tbl_items.setItem(row_idx, 4, QTableWidgetItem(f"{item['alch_value']:,}"))
            self.tbl_items.setItem(row_idx, 5, QTableWidgetItem(f"{item['nat_cost']:,}"))
            self.tbl_items.setItem(row_idx, 6, p_item)
            self.tbl_items.setItem(row_idx, 7, vol_item)
            self.tbl_items.setItem(row_idx, 8, QTableWidgetItem(f"{item['limit']:,}" if item['limit'] > 0 else "N/A"))

    def render_history_table_view(self):
        self._loading_history = True
        self.tbl_history.setRowCount(0)

        headers = ["Time", "Item Name", "Qty", "Cost Paid", "Nat Cost", "Batch Profit"] + self.profiles
        self.tbl_history.setColumnCount(len(headers))
        self.tbl_history.setHorizontalHeaderLabels(headers)
        widths = [130, 140, 50, 75, 85]
        for i, w in enumerate(widths): self.tbl_history.setColumnWidth(i, w)
        for i in range(5, len(headers)): self.tbl_history.setColumnWidth(i, 60)

        selected_profile = self.cmb_profile_filter.currentText()
        for log in self.history_logs:
            if selected_profile != "All" and not log['profiles'].get(selected_profile, False):
                continue

            r = self.tbl_history.rowCount()
            self.tbl_history.insertRow(r)

            t_item = QTableWidgetItem(log['time'])
            t_item.setFlags(t_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            t_item.setData(Qt.ItemDataRole.UserRole, id(log))
            
            n_item = QTableWidgetItem(log['name'])
            n_item.setFlags(n_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            p_val = log['batch_profit']
            p_item = QTableWidgetItem(f"{p_val:,}")
            p_item.setFlags(p_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            p_item.setForeground(QColor('#00ff00' if p_val > 0 else '#ff3333'))

            nc_item = QTableWidgetItem(f"{log.get('nat_cost', 0):,}")
            nc_item.setFlags(nc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.tbl_history.setItem(r, 0, t_item)
            self.tbl_history.setItem(r, 1, n_item)
            self.tbl_history.setItem(r, 2, QTableWidgetItem(f"{log['qty']:,}"))
            self.tbl_history.setItem(r, 3, QTableWidgetItem(f"{log['cost_paid']:,}"))
            self.tbl_history.setItem(r, 4, nc_item)
            self.tbl_history.setItem(r, 5, p_item)

            for col_idx, profile_name in enumerate(self.profiles, start=6):
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                state = Qt.CheckState.Checked if log['profiles'].get(profile_name, False) else Qt.CheckState.Unchecked
                chk.setCheckState(state)
                self.tbl_history.setItem(r, col_idx, chk)

        self._loading_history = False

    def handle_log_edit(self, row, col):
        if self._loading_history: return
        item = self.tbl_history.item(row, col)
        t_item = self.tbl_history.item(row, 0)
        if not item or not t_item: return

        log_id = t_item.data(Qt.ItemDataRole.UserRole)
        target_log = next((log for log in self.history_logs if id(log) == log_id), None)
        if not target_log: return

        if col >= 6:
            prof_header = self.tbl_history.horizontalHeaderItem(col).text()
            target_log['profiles'][prof_header] = (item.checkState() == Qt.CheckState.Checked)
        elif col in [2, 3]:
            try: new_val = int(item.text().replace(',', '').strip())
            except ValueError: return  

            old_qty = target_log['qty']
            old_cost = target_log['cost_paid']
            profit_per_item = target_log['batch_profit'] / old_qty if old_qty > 0 else 0
            base_value = profit_per_item + old_cost  
            
            if col == 2: target_log['qty'] = new_val
            elif col == 3: target_log['cost_paid'] = new_val

            new_profit = int((base_value - target_log['cost_paid']) * target_log['qty'])
            target_log['batch_profit'] = new_profit

            self.tbl_history.blockSignals(True)
            p_item = self.tbl_history.item(row, 5)
            if p_item:
                p_item.setText(f"{new_profit:,}")
                p_item.setForeground(QColor('#00ff00' if new_profit > 0 else '#ff3333'))
            self.tbl_history.blockSignals(False)

        self.recalculate_global_aggregates()
        FileHandler.save_history(self.history_logs, self.profiles)

    def duplicate_selected_history_row(self):
        ranges = self.tbl_history.selectedRanges()
        if not ranges: return
        row = ranges[0].topRow()
        try:
            new_log = {
                'time': self.tbl_history.item(row, 0).text(),
                'name': self.tbl_history.item(row, 1).text(),
                'qty': int(self.tbl_history.item(row, 2).text().replace(',', '')),
                'cost_paid': int(self.tbl_history.item(row, 3).text().replace(',', '')),
                'nat_cost': int(self.tbl_history.item(row, 4).text().replace(',', '')),
                'batch_profit': int(self.tbl_history.item(row, 5).text().replace(',', '')),
                'profiles': {p: False for p in self.profiles}
            }
            self.history_logs.append(new_log)
            self.render_history_table_view()
            self.recalculate_global_aggregates()
            FileHandler.save_history(self.history_logs, self.profiles)
        except Exception: pass

    def delete_selected_history_row(self):
        ranges = self.tbl_history.selectedRanges()
        if not ranges: return
        row = ranges[0].topRow()
        
        t_item = self.tbl_history.item(row, 0)
        n_item = self.tbl_history.item(row, 1)
        if not t_item or not n_item: return

        if QMessageBox.question(self, "Confirm Delete", f"Delete log for '{n_item.text()}'?") == QMessageBox.StandardButton.Yes:
            log_id = t_item.data(Qt.ItemDataRole.UserRole)
            self.history_logs = [log for log in self.history_logs if id(log) != log_id]
            self.render_history_table_view()
            self.recalculate_global_aggregates()
            FileHandler.save_history(self.history_logs, self.profiles)

    def trigger_fix_math(self):
        if not self.calculated_items_cache:
            QMessageBox.warning(self, "Missing Data", "Sync Live Wiki Data first.")
            return
            
        fixed = AlchCalculator.fix_historical_profits(self.history_logs, self.calculated_items_cache)
        if fixed > 0:
            self.render_history_table_view()
            self.recalculate_global_aggregates()
            FileHandler.save_history(self.history_logs, self.profiles)
            QMessageBox.information(self, "Scrub Complete", f"Fixed {fixed} entries!")
        else:
            QMessageBox.information(self, "All Good", "All profits are mathematically correct.")

    def open_logging_dialog(self, row, column):
        name_item = self.tbl_items.item(row, 0)
        if not name_item: return
        
        try:
            default_cost = int(self.tbl_items.item(row, 3).text().replace(',', ''))
            alch_val = int(self.tbl_items.item(row, 4).text().replace(',', ''))
            nat_cost = int(self.tbl_items.item(row, 5).text().replace(',', ''))
        except ValueError: return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Log: {name_item.text()}")
        form = QFormLayout(dialog)
        qty_input = QLineEdit("70")
        cost_input = QLineEdit(str(default_cost))
        form.addRow("Quantity:", qty_input)
        form.addRow("Custom Buy Price:", cost_input)

        buttons = QHBoxLayout()
        btn_confirm = QPushButton("Add to Log")
        btn_confirm.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_confirm)
        buttons.addWidget(btn_cancel)
        form.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                qty = int(qty_input.text().replace(',', '').strip())
                custom_cost = int(cost_input.text().replace(',', '').strip())
            except ValueError: return

            new_log = {
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'name': name_item.text(),
                'qty': qty,
                'cost_paid': custom_cost,
                'nat_cost': nat_cost,
                'batch_profit': (alch_val - (custom_cost + nat_cost)) * qty,
                'profiles': {p: False for p in self.profiles}
            }
            self.history_logs.append(new_log)
            self.render_history_table_view()
            self.recalculate_global_aggregates()
            FileHandler.save_history(self.history_logs, self.profiles)

    def prompt_add_profile(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Profile")
        layout = QFormLayout(dialog)
        name_input = QLineEdit()
        layout.addRow("Account Name:", name_input)
        btn = QPushButton("Save")
        btn.clicked.connect(dialog.accept)
        layout.addRow(btn)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_input.text().strip()
            if name and name not in self.profiles:
                self.profiles.append(name)
                for log in self.history_logs: log['profiles'][name] = False
                self.update_profile_dropdowns()
                self.render_history_table_view()
                FileHandler.save_profiles(self.profiles)
                FileHandler.save_history(self.history_logs, self.profiles)

    def delete_active_profile(self):
        selected = self.cmb_profile_filter.currentText()
        if selected == "All": return

        if QMessageBox.question(self, "Confirm Deletion", f"Wipe out profile '{selected}'?") == QMessageBox.StandardButton.Yes:
            self.profiles.remove(selected)
            for log in self.history_logs:
                if selected in log['profiles']: del log['profiles'][selected]
            self.update_profile_dropdowns()
            self.render_history_table_view()
            FileHandler.save_profiles(self.profiles)
            FileHandler.save_history(self.history_logs, self.profiles)

    def update_profile_dropdowns(self):
        self.cmb_profile_filter.blockSignals(True)
        current = self.cmb_profile_filter.currentText()
        self.cmb_profile_filter.clear()
        self.cmb_profile_filter.addItem("All")
        self.cmb_profile_filter.addItems(self.profiles)
        if self.cmb_profile_filter.findText(current) != -1:
            self.cmb_profile_filter.setCurrentText(current)
        self.cmb_profile_filter.blockSignals(False)

    def handle_profile_filter_changed(self):
        self.render_history_table_view()
        self.recalculate_global_aggregates()

    def recalculate_global_aggregates(self):
        selected_profile = self.cmb_profile_filter.currentText()
        total_casts = total_profit = 0

        for log in self.history_logs:
            if selected_profile != "All" and not log['profiles'].get(selected_profile, False):
                continue
            total_casts += log.get('qty', 0)
            total_profit += log.get('batch_profit', 0)

        self.txt_total_casts.blockSignals(True)
        self.txt_total_profit.blockSignals(True)
        self.txt_total_xp.blockSignals(True)
        
        self.txt_total_casts.setText(f"{total_casts:,}")
        self.txt_total_profit.setText(f"{total_profit:,}")
        self.txt_total_xp.setText(f"{int(total_casts * MAGIC_XP_PER_CAST):,}")
        
        self.txt_total_casts.blockSignals(False)
        self.txt_total_profit.blockSignals(False)
        self.txt_total_xp.blockSignals(False)

    def handle_manual_override(self, text):
        sender = self.sender()
        if not sender: return
        clean = text.replace(',', '').strip()
        if sender == self.txt_total_casts and clean.isdigit():
            self.txt_total_xp.blockSignals(True)
            self.txt_total_xp.setText(f"{int(int(clean) * MAGIC_XP_PER_CAST):,}")
            self.txt_total_xp.blockSignals(False)

    def reset_tracker(self):
        if QMessageBox.question(self, "Reset Tracker", "Wipe all records?") == QMessageBox.StandardButton.Yes:
            self.history_logs.clear()
            self.render_history_table_view()
            self.recalculate_global_aggregates()
            FileHandler.purge_history_file()
            QMessageBox.information(self, "Tracker Reset", "Data modules reset.")