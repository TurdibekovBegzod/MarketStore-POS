from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QSpinBox, QMessageBox, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt
import database as db
from ui.i18n import set_language


class StockWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Mahsulot qidirish...")
        self.search_edit.setFixedHeight(38)
        self.search_edit.setStyleSheet(
            "border:1px solid #d1d5db;border-radius:6px;padding:0 12px;font-size:13px;background:white;"
        )
        self.search_edit.textChanged.connect(self.load_data)
        toolbar.addWidget(self.search_edit)
        toolbar.addStretch()

        incoming_btn = QPushButton("+ Kirim qo'shish")
        incoming_btn.setFixedHeight(38)
        incoming_btn.setStyleSheet(
            "background:#059669;color:white;border:none;border-radius:6px;padding:0 16px;font-weight:bold;font-size:13px;"
        )
        incoming_btn.clicked.connect(self._add_stock)
        toolbar.addWidget(incoming_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Mahsulot", "Qoldiq", "Amal"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 150)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;}"
            " QTableWidget::item{padding:7px 10px;}"
            " QHeaderView::section{background:#f8fafc;border:none;border-bottom:1px solid #e2e8f0;padding:8px;font-weight:bold;color:#64748b;}"
            " QTableWidget::item:alternate{background:#f8fafc;}"
        )
        self.table.verticalHeader().setDefaultSectionSize(56)
        layout.addWidget(self.table)

    def load_data(self):
        query = self.search_edit.text() if hasattr(self, "search_edit") else ""
        products = db.search_products(query) if query else db.get_all_products()
        self.table.setRowCount(0)
        for row, product in enumerate(products):
            self.table.insertRow(row)
            name_item = QTableWidgetItem(product["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, dict(product))
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(f"{product['stock']} {product['unit']}"))

            btn = QPushButton("+ Kirim")
            btn.setMinimumWidth(94)
            btn.setFixedHeight(30)
            btn.setStyleSheet(
                "background:#ecfdf5;color:#065f46;border:1px solid #6ee7b7;"
                "border-radius:6px;padding:4px 10px;font-size:12px;font-weight:bold;"
            )
            btn.clicked.connect(lambda _, r=row: self._quick_add(r))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(10, 4, 10, 4)
            actions_layout.addStretch()
            actions_layout.addWidget(btn)
            actions_layout.addStretch()
            self.table.setCellWidget(row, 2, actions_widget)
            self.table.setRowHeight(row, 56)
        set_language(self, self.property("app_language") or "uz")

    def _add_stock(self):
        dlg = StockInDialog(self)
        if dlg.exec():
            self.load_data()

    def _quick_add(self, row):
        item = self.table.item(row, 0)
        if not item:
            return
        product = item.data(Qt.ItemDataRole.UserRole)
        dlg = StockInDialog(self, product)
        if dlg.exec():
            self.load_data()


class StockInDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.setWindowTitle("Kirim qo'shish")
        self.setFixedWidth(380)
        self.setStyleSheet("QDialog{background:white;} QLabel{color:#374151;font-size:13px;}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)

        form = QFormLayout()
        form.setSpacing(10)
        self.product_combo = QComboBox()
        self.product_combo.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:6px 10px;font-size:13px;")
        for product_row in db.get_all_products():
            self.product_combo.addItem(product_row["name"], product_row["id"])
        if product:
            idx = self.product_combo.findData(product["id"])
            if idx >= 0:
                self.product_combo.setCurrentIndex(idx)
        form.addRow("Mahsulot:", self.product_combo)

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999999)
        self.qty_spin.setValue(1)
        self.qty_spin.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:6px 10px;font-size:13px;")
        form.addRow("Miqdor:", self.qty_spin)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Ixtiyoriy izoh")
        self.note_edit.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:6px 10px;font-size:13px;")
        form.addRow("Izoh:", self.note_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Bekor")
        cancel_btn.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:8px 16px;color:#6b7280;background:white;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Kirim qo'shish")
        save_btn.setStyleSheet("background:#059669;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;")
        save_btn.clicked.connect(self._save)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        product_id = self.product_combo.currentData()
        quantity = self.qty_spin.value()
        note = self.note_edit.text()
        db.add_stock(product_id, quantity, note)
        QMessageBox.information(self, "Muvaffaqiyat", f"{quantity} ta mahsulot qo'shildi!")
        self.accept()
