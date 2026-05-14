from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QMessageBox, QHeaderView, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt
import database as db
from ui.i18n import set_language


class PartyDialog(QDialog):
    def __init__(self, parent=None, party=None, label="Ta'minotchi"):
        super().__init__(parent)
        self.party = party
        self.label = label
        self.setWindowTitle(f"{label} qo'shish" if not party else f"{label}ni tahrirlash")
        self.setFixedWidth(380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        form = QFormLayout()
        self.name_edit = QLineEdit(self.party["name"] if self.party else "")
        self.phone_edit = QLineEdit(self.party["phone"] if self.party and self.party["phone"] else "")
        self.note_edit = QLineEdit(self.party["note"] if self.party and self.party["note"] else "")
        self.currency_combo = QComboBox()
        for currency in db.get_currencies():
            self.currency_combo.addItem(currency["code"], currency["code"])
        current_currency = self.party["debt_currency"] if self.party and self.party["debt_currency"] else "UZS"
        idx = self.currency_combo.findData(current_currency)
        if idx >= 0:
            self.currency_combo.setCurrentIndex(idx)
        if self.party and (self.party["balance"] or 0) > 0:
            self.currency_combo.setEnabled(False)
        for widget in [self.name_edit, self.phone_edit, self.note_edit, self.currency_combo]:
            widget.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:7px 10px;background:white;")
        form.addRow("Nomi *:", self.name_edit)
        form.addRow("Telefon:", self.phone_edit)
        form.addRow("Qarz valyutasi:", self.currency_combo)
        form.addRow("Izoh:", self.note_edit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        cancel_btn = QPushButton("Bekor")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Saqlash")
        save_btn.setStyleSheet("background:#3b82f6;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;")
        save_btn.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Xatolik", f"{self.label} nomini kiriting!")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip() or None,
            "note": self.note_edit.text().strip() or None,
            "debt_currency": self.currency_combo.currentData(),
        }


class DebtDialog(QDialog):
    def __init__(self, parent=None, title="Qarz", currency_code="UZS"):
        super().__init__(parent)
        self.currency_code = currency_code
        self.setWindowTitle(title)
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        form = QFormLayout()
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(f" {self.currency_code}")
        self.amount_spin.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:7px 10px;background:white;")
        form.addRow("Summa:", self.amount_spin)
        layout.addLayout(form)

        btns = QHBoxLayout()
        cancel_btn = QPushButton("Bekor")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Saqlash")
        save_btn.setStyleSheet("background:#059669;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;")
        save_btn.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _save(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Xatolik", "Summani kiriting!")
            return
        self.accept()


class DebtHistoryDialog(QDialog):
    def __init__(self, parent=None, party=None, kind="supplier"):
        super().__init__(parent)
        self.party = party
        self.kind = kind
        self.setWindowTitle(f"To'lov tarixi - {party['name']}")
        self.setMinimumSize(720, 420)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel(
            f"{self.party['name']} | Joriy qarz: "
            f"{self.party['balance']:,.2f} {self.party['debt_currency'] or 'UZS'}"
        )
        header.setStyleSheet("font-size:14px;font-weight:bold;color:#1e293b;")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Vaqt", "Amal", "Summa", "Valyuta", "Izoh"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 170)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self._table_style())
        layout.addWidget(self.table)

        close_btn = QPushButton("Yopish")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def load_data(self):
        self.table.setRowCount(0)
        currency = self.party["debt_currency"] or "UZS"
        movements = (
            db.get_supplier_debt_movements(self.party["id"])
            if self.kind == "supplier"
            else db.get_debtor_debt_movements(self.party["id"])
        )
        for row, movement in enumerate(movements):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(movement["created_at"] or ""))
            if self.kind == "supplier":
                action = "Qarz olindi" if movement["type"] == "qarz" else "To'landi"
            else:
                action = "Qarz berildi" if movement["type"] == "qarz" else "Qaytarildi"
            self.table.setItem(row, 1, QTableWidgetItem(action))
            amount_item = QTableWidgetItem(f"{movement['amount']:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, amount_item)
            self.table.setItem(row, 3, QTableWidgetItem(currency))
            self.table.setItem(row, 4, QTableWidgetItem(movement["note"] or ""))

    def _table_style(self):
        return """
            QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;}
            QTableWidget::item{padding:7px 10px;}
            QHeaderView::section{background:#f8fafc;border:none;border-bottom:1px solid #e2e8f0;padding:8px;font-weight:bold;color:#64748b;}
            QTableWidget::item:alternate{background:#f8fafc;}
        """


class SupplierDebtsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tables = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        self.total_lbl = QLabel()
        self.total_lbl.setStyleSheet("font-size:14px;font-weight:bold;color:#1e293b;")
        toolbar.addWidget(self.total_lbl)
        toolbar.addStretch()
        self.add_btn = QPushButton()
        self.add_btn.setFixedHeight(36)
        self.add_btn.setStyleSheet("background:#3b82f6;color:white;border:none;border-radius:6px;padding:0 14px;font-weight:bold;")
        self.add_btn.clicked.connect(self._add_current_party)
        toolbar.addWidget(self.add_btn)
        layout.addLayout(toolbar)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_table("supplier"), "Olgan qarzlar")
        self.tabs.addTab(self._build_table("debtor"), "Bergan qarzlar")
        self.tabs.currentChanged.connect(self._update_toolbar)
        layout.addWidget(self.tabs)
        self._update_toolbar()

    def _build_table(self, kind):
        table = QTableWidget()
        table.setColumnCount(6)
        total_header = "Jami olingan" if kind == "supplier" else "Jami berilgan"
        table.setHorizontalHeaderLabels(["Nomi", "Telefon", "Valyuta", "Qarz", total_header, "Amallar"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in [(1, 150), (2, 80), (3, 140), (4, 140), (5, 430)]:
            table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(column, width)
        table.verticalHeader().setDefaultSectionSize(54)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(self._table_style())
        self.tables[kind] = table
        return table

    def load_data(self):
        self._load_table("supplier", db.get_all_suppliers())
        self._load_table("debtor", db.get_all_debtors())
        self._update_toolbar()
        set_language(self, self.property("app_language") or "uz")

    def _load_table(self, kind, rows):
        table = self.tables[kind]
        table.setRowCount(0)
        for row, party in enumerate(rows):
            table.insertRow(row)
            name_item = QTableWidgetItem(party["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, dict(party))
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(party["phone"] or ""))
            table.setItem(row, 2, QTableWidgetItem(party["debt_currency"] or "UZS"))
            table.setItem(row, 3, self._money_item(party["balance"] or 0, party["debt_currency"] or "UZS"))
            total_key = "total_received" if kind == "supplier" else "total_given"
            table.setItem(row, 4, self._money_item(party[total_key] or 0, party["debt_currency"] or "UZS"))
            table.setCellWidget(row, 5, self._actions_widget(row, kind))
            table.setRowHeight(row, 54)

    def _actions_widget(self, row, kind):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        plus_btn = QPushButton("+")
        minus_btn = QPushButton("-")
        history_btn = QPushButton("Tarix")
        edit_btn = QPushButton("Tahrir")
        delete_btn = QPushButton("O'chir")
        for btn in [plus_btn, minus_btn, history_btn, edit_btn, delete_btn]:
            btn.setFixedHeight(30)
        plus_btn.setFixedWidth(38)
        minus_btn.setFixedWidth(38)
        history_btn.setFixedWidth(82)
        edit_btn.setFixedWidth(86)
        delete_btn.setFixedWidth(90)
        plus_btn.setStyleSheet(self._button_style("#ecfdf5", "#065f46", "#6ee7b7", "#10b981"))
        minus_btn.setStyleSheet(self._button_style("#fef2f2", "#b91c1c", "#fca5a5", "#ef4444"))
        history_btn.setStyleSheet(self._button_style("#eff6ff", "#1d4ed8", "#93c5fd", "#3b82f6"))
        edit_btn.setStyleSheet(self._button_style("#fff7ed", "#9a3412", "#fdba74", "#fb923c"))
        delete_btn.setStyleSheet(self._button_style("#fef2f2", "#991b1b", "#fca5a5", "#dc2626"))
        plus_btn.clicked.connect(lambda _, r=row, k=kind: self._change_debt(r, k, "plus"))
        minus_btn.clicked.connect(lambda _, r=row, k=kind: self._change_debt(r, k, "minus"))
        history_btn.clicked.connect(lambda _, r=row, k=kind: self._show_history(r, k))
        edit_btn.clicked.connect(lambda _, r=row, k=kind: self._edit_party(r, k))
        delete_btn.clicked.connect(lambda _, r=row, k=kind: self._delete_party(r, k))
        for btn in [plus_btn, minus_btn, history_btn, edit_btn, delete_btn]:
            layout.addWidget(btn)
        return widget

    def _current_kind(self):
        return "supplier" if self.tabs.currentIndex() == 0 else "debtor"

    def _label_for(self, kind):
        return "Ta'minotchi" if kind == "supplier" else "Qarz oluvchi"

    def _party_at_row(self, row, kind):
        item = self.tables[kind].item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _update_toolbar(self):
        kind = self._current_kind()
        rows = db.get_all_suppliers() if kind == "supplier" else db.get_all_debtors()
        totals = {}
        for party in rows:
            currency = party["debt_currency"] or "UZS"
            totals[currency] = totals.get(currency, 0) + (party["balance"] or 0)
        total_text = " | ".join(f"{amount:,.2f} {currency}" for currency, amount in totals.items()) or "0 UZS"
        title = "Umumiy olingan qarz" if kind == "supplier" else "Umumiy berilgan qarz"
        self.total_lbl.setText(f"{title}: {total_text}")
        self.add_btn.setText("+ Ta'minotchi" if kind == "supplier" else "+ Qarz oluvchi")

    def _add_current_party(self):
        kind = self._current_kind()
        dlg = PartyDialog(self, label=self._label_for(kind))
        if dlg.exec():
            data = dlg.get_data()
            if kind == "supplier":
                db.add_supplier(data["name"], data["phone"], data["note"], data["debt_currency"])
            else:
                db.add_debtor(data["name"], data["phone"], data["note"], data["debt_currency"])
            self.load_data()

    def _edit_party(self, row, kind):
        party = self._party_at_row(row, kind)
        if not party:
            return
        dlg = PartyDialog(self, party, self._label_for(kind))
        if dlg.exec():
            data = dlg.get_data()
            if kind == "supplier":
                db.update_supplier(party["id"], data["name"], data["phone"], data["note"], data["debt_currency"])
            else:
                db.update_debtor(party["id"], data["name"], data["phone"], data["note"], data["debt_currency"])
            self.load_data()

    def _change_debt(self, row, kind, mode):
        party = self._party_at_row(row, kind)
        if not party:
            return
        if kind == "supplier":
            title = "Qarzni oshirish" if mode == "plus" else "Qarzni kamaytirish"
        else:
            title = "Qarz berish" if mode == "plus" else "Qarz qaytarildi"
        currency = party["debt_currency"] or "UZS"
        dlg = DebtDialog(self, title, currency)
        if dlg.exec():
            amount = dlg.amount_spin.value()
            if kind == "supplier" and mode == "plus":
                db.add_supplier_debt(party["id"], amount, f"{party['name']}dan qarz olindi")
            elif kind == "supplier":
                db.pay_supplier_debt(party["id"], amount, f"{party['name']}ga to'landi")
            elif mode == "plus":
                db.add_debtor_debt(party["id"], amount, f"{party['name']}ga qarz berildi")
            else:
                db.pay_debtor_debt(party["id"], amount, f"{party['name']}dan qaytarildi")
            self.load_data()

    def _show_history(self, row, kind):
        party = self._party_at_row(row, kind)
        if not party:
            return
        dlg = DebtHistoryDialog(self, party, kind)
        dlg.exec()

    def _delete_party(self, row, kind):
        party = self._party_at_row(row, kind)
        if not party:
            return
        if kind == "supplier":
            title = "Ta'minotchini o'chirish"
            text = f"'{party['name']}' o'chirilsinmi?\n\nMahsulotlar o'chmaydi, faqat 'Kimdan olingan' maydoni bo'shatiladi."
        else:
            title = "Qarz oluvchini o'chirish"
            text = f"'{party['name']}' va uning qarz tarixi o'chirilsinmi?"
        reply = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if kind == "supplier":
                db.delete_supplier(party["id"])
            else:
                db.delete_debtor(party["id"])
            self.load_data()

    def _money_item(self, value, currency="UZS"):
        item = QTableWidgetItem(f"{value:,.2f} {currency}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item

    def _table_style(self):
        return """
            QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;}
            QTableWidget::item{padding:7px 10px;}
            QHeaderView::section{background:#f8fafc;border:none;border-bottom:1px solid #e2e8f0;padding:8px;font-weight:bold;color:#64748b;}
            QTableWidget::item:alternate{background:#f8fafc;}
        """

    def _button_style(self, bg, fg, border, hover):
        return f"""
            QPushButton {{
                background:{bg};
                color:{fg};
                border:1px solid {border};
                border-radius:6px;
                font-weight:bold;
            }}
            QPushButton:hover {{
                background:{hover};
                color:white;
                border-color:{hover};
            }}
            QPushButton:pressed {{
                background:#1e293b;
                color:white;
                border-color:#1e293b;
                padding-top:2px;
            }}
        """
