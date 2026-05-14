from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDoubleSpinBox,
    QMessageBox, QHeaderView, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
import database as db
from ui.i18n import set_language


class ExpenseChart(QWidget):
    def __init__(self):
        super().__init__()
        self.points = []
        self.title = "Harajatlar grafigi"
        self.setMinimumHeight(230)
        self.setStyleSheet("background:white;border:1px solid #e2e8f0;border-radius:8px;")

    def set_points(self, points, title):
        self.points = points
        self.title = title
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(16, 14, -16, -14)
        painter.setPen(QColor("#1e293b"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(rect.left(), rect.top(), self.title)
        chart = rect.adjusted(42, 28, -10, -28)
        painter.setPen(QPen(QColor("#e2e8f0"), 1))
        painter.drawLine(chart.bottomLeft(), chart.bottomRight())
        painter.drawLine(chart.bottomLeft(), chart.topLeft())
        if not self.points:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(chart, Qt.AlignmentFlag.AlignCenter, "Ma'lumot yo'q")
            return
        max_value = max(value for _, value in self.points) or 1
        count = max(len(self.points) - 1, 1)
        plotted = []
        for index, (_, value) in enumerate(self.points):
            x = chart.left() + (index / count) * chart.width()
            y = chart.bottom() - (value / max_value) * chart.height()
            plotted.append(QPointF(x, y))
        painter.setPen(QPen(QColor("#ef4444"), 3))
        for index in range(1, len(plotted)):
            painter.drawLine(plotted[index - 1], plotted[index])
        painter.setBrush(QColor("#ef4444"))
        painter.setPen(QPen(QColor("white"), 2))
        for point in plotted:
            painter.drawEllipse(point, 4, 4)
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(chart.left() - 40, chart.top() + 8, f"{max_value:,.0f}")
        painter.drawText(chart.left() - 20, chart.bottom(), "0")
        painter.drawText(chart.left(), chart.bottom() + 20, self.points[0][0])
        painter.drawText(chart.right() - 70, chart.bottom() + 20, self.points[-1][0])


class ExpenseDialog(QDialog):
    def __init__(self, parent=None, expense=None):
        super().__init__(parent)
        self.expense = expense
        self.setWindowTitle("Harajat qo'shish" if not expense else "Harajatni tahrirlash")
        self.setFixedWidth(420)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        form = QFormLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItem("— Kategoriya —", None)
        for category in db.get_expense_categories():
            self.category_combo.addItem(category["name"], category["id"])
        if self.expense and self.expense["category_id"]:
            idx = self.category_combo.findData(self.expense["category_id"])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(self.expense["amount"] if self.expense else 0)
        self.currency_combo = QComboBox()
        for currency in db.get_currencies():
            self.currency_combo.addItem(currency["code"], currency["code"])
        if self.expense and self.expense["currency_code"]:
            idx = self.currency_combo.findData(self.expense["currency_code"])
            if idx >= 0:
                self.currency_combo.setCurrentIndex(idx)
        self.currency_combo.currentIndexChanged.connect(self._update_suffix)
        self.description_edit = QLineEdit(self.expense["description"] if self.expense and self.expense["description"] else "")
        self.description_edit.setPlaceholderText("Masalan: ofis ijara, yoqilg'i, reklama")
        for widget in [self.category_combo, self.amount_spin, self.currency_combo, self.description_edit]:
            widget.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:7px 10px;background:white;")
        form.addRow("Kategoriya:", self.category_combo)
        form.addRow("Summa:", self.amount_spin)
        form.addRow("Valyuta:", self.currency_combo)
        form.addRow("Description:", self.description_edit)
        layout.addLayout(form)
        self._update_suffix()

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

    def _update_suffix(self):
        self.amount_spin.setSuffix(f" {self.currency_combo.currentData() or 'UZS'}")

    def _save(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Xatolik", "Summani kiriting!")
            return
        self.accept()

    def get_data(self):
        return {
            "category_id": self.category_combo.currentData(),
            "amount": self.amount_spin.value(),
            "currency_code": self.currency_combo.currentData() or "UZS",
            "description": self.description_edit.text().strip() or None,
        }


class CategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.setWindowTitle("Kategoriya qo'shish" if not category else "Kategoriya tahrirlash")
        self.setFixedWidth(320)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self.name_edit = QLineEdit(category["name"] if category else "")
        self.name_edit.setPlaceholderText("Kategoriya nomi")
        self.name_edit.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:7px 10px;background:white;")
        layout.addWidget(self.name_edit)
        btns = QHBoxLayout()
        cancel_btn = QPushButton("Bekor")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Saqlash")
        save_btn.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def _save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Xatolik", "Kategoriya nomini kiriting!")
            return
        self.accept()


class CategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Harajat kategoriyalari")
        self.setMinimumSize(520, 420)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ Kategoriya")
        add_btn.clicked.connect(self._add_category)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Nomi", "Amallar"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 210)
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for row, category in enumerate(db.get_expense_categories()):
            self.table.insertRow(row)
            item = QTableWidgetItem(category["name"])
            item.setData(Qt.ItemDataRole.UserRole, dict(category))
            self.table.setItem(row, 0, item)
            self.table.setCellWidget(row, 1, self._actions_widget(row))
            self.table.setRowHeight(row, 54)

    def _actions_widget(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        edit_btn = QPushButton("✏ Tahrir")
        del_btn = QPushButton("🗑 O'chir")
        edit_btn.setFixedSize(92, 30)
        del_btn.setFixedSize(96, 30)
        edit_btn.clicked.connect(lambda _, r=row: self._edit_category(r))
        del_btn.clicked.connect(lambda _, r=row: self._delete_category(r))
        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)
        return widget

    def _category_at_row(self, row):
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_category(self):
        dlg = CategoryDialog(self)
        if dlg.exec():
            try:
                db.add_expense_category(dlg.name_edit.text().strip())
                self.load_data()
            except db.AppError as exc:
                QMessageBox.warning(self, "Saqlanmadi", str(exc))

    def _edit_category(self, row):
        category = self._category_at_row(row)
        if not category:
            return
        dlg = CategoryDialog(self, category)
        if dlg.exec():
            try:
                db.update_expense_category(category["id"], dlg.name_edit.text().strip())
                self.load_data()
            except db.AppError as exc:
                QMessageBox.warning(self, "Saqlanmadi", str(exc))

    def _delete_category(self, row):
        category = self._category_at_row(row)
        if not category:
            return
        reply = QMessageBox.question(
            self, "Kategoriya o'chirish",
            f"'{category['name']}' o'chirilsinmi?\nHarajatlar o'chmaydi, kategoriyasi bo'shatiladi.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_expense_category(category["id"])
            self.load_data()


class ExpenseReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Harajatlar hisoboti")
        self.setMinimumSize(820, 560)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Sana:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self.load_data)
        toolbar.addWidget(self.date_edit)
        self.period_combo = QComboBox()
        self.period_combo.addItem("Kunlik", "day")
        self.period_combo.addItem("Haftalik", "week")
        self.period_combo.addItem("Oylik", "month")
        self.period_combo.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.period_combo)
        self.category_filter = QComboBox()
        self.category_filter.setMinimumWidth(190)
        self.category_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.category_filter)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.total_lbl = QLabel()
        self.total_lbl.setStyleSheet("font-size:14px;font-weight:bold;color:#1e293b;")
        layout.addWidget(self.total_lbl)
        self.chart = ExpenseChart()
        layout.addWidget(self.chart)
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Kategoriya", "Valyuta", "Summa"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.category_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.category_table.setAlternatingRowColors(True)
        layout.addWidget(self.category_table)
        self._load_category_filter()

    def load_data(self):
        start_date, end_date = self._date_range()
        category_id = self.category_filter.currentData() if hasattr(self, "category_filter") else None
        rows = db.get_expense_report(start_date, end_date, category_id)
        totals = {}
        by_label = {}
        for row in rows:
            currency = row["currency_code"] or "UZS"
            totals[currency] = totals.get(currency, 0) + (row["amount"] or 0)
            by_label[row["label"]] = by_label.get(row["label"], 0) + (row["amount"] or 0)
        total_text = " | ".join(f"{amount:,.2f} {currency}" for currency, amount in totals.items()) or "0 UZS"
        self.total_lbl.setText(f"Jami harajat: {total_text}")
        self.chart.set_points(self._filled_points(by_label, start_date, end_date), "Davr bo'yicha harajatlar")
        self._load_category_report(start_date, end_date, category_id)

    def _load_category_filter(self):
        current = self.category_filter.currentData() if hasattr(self, "category_filter") else None
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("Barcha kategoriyalar", None)
        for category in db.get_expense_categories():
            self.category_filter.addItem(category["name"], category["id"])
        if current:
            idx = self.category_filter.findData(current)
            if idx >= 0:
                self.category_filter.setCurrentIndex(idx)
        self.category_filter.blockSignals(False)

    def _load_category_report(self, start_date, end_date, category_id=None):
        self.category_table.setRowCount(0)
        for row, item in enumerate(db.get_expense_category_report(start_date, end_date, category_id)):
            self.category_table.insertRow(row)
            self.category_table.setItem(row, 0, QTableWidgetItem(item["category_name"]))
            self.category_table.setItem(row, 1, QTableWidgetItem(item["currency_code"] or "UZS"))
            amount_item = QTableWidgetItem(f"{item['amount']:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.category_table.setItem(row, 2, amount_item)

    def _date_range(self):
        selected = self.date_edit.date().toPyDate()
        period = self.period_combo.currentData()
        if period == "day":
            start = end = selected
        elif period == "month":
            start = selected.replace(day=1)
            if selected.month == 12:
                end = selected.replace(year=selected.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = selected.replace(month=selected.month + 1, day=1) - timedelta(days=1)
        else:
            start = selected - timedelta(days=selected.weekday())
            end = start + timedelta(days=6)
        return start.isoformat(), end.isoformat()

    def _filled_points(self, by_label, start_date, end_date):
        current = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        points = []
        while current <= end:
            label = current.isoformat()
            points.append((label[5:], by_label.get(label, 0)))
            current += timedelta(days=1)
        return points


class ExpensesWidget(QWidget):
    def __init__(self):
        super().__init__()
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
        category_btn = QPushButton("Kategoriyalar")
        category_btn.clicked.connect(self._manage_categories)
        add_btn = QPushButton("+ Harajat")
        add_btn.clicked.connect(self._add_expense)
        report_btn = QPushButton("Hisobotlar")
        report_btn.clicked.connect(self._show_report)
        for btn in [category_btn, add_btn, report_btn]:
            btn.setFixedHeight(36)
            btn.setStyleSheet(self._button_style())
            toolbar.addWidget(btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Vaqt", "Kategoriya", "Summa", "Valyuta", "Description", "Amallar"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for column, width in [(0, 160), (1, 150), (2, 130), (3, 90), (5, 240)]:
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(column, width)
        self.table.verticalHeader().setDefaultSectionSize(54)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self._table_style())
        layout.addWidget(self.table)

    def load_data(self):
        expenses = db.get_expenses()
        totals = {}
        for expense in expenses:
            currency = expense["currency_code"] or "UZS"
            totals[currency] = totals.get(currency, 0) + (expense["amount"] or 0)
        total_text = " | ".join(f"{amount:,.2f} {currency}" for currency, amount in totals.items()) or "0 UZS"
        self.total_lbl.setText(f"Jami harajat: {total_text}")
        self.table.setRowCount(0)
        for row, expense in enumerate(expenses):
            self.table.insertRow(row)
            item = QTableWidgetItem(expense["created_at"] or "")
            item.setData(Qt.ItemDataRole.UserRole, dict(expense))
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(expense["category_name"] or ""))
            amount_item = QTableWidgetItem(f"{expense['amount']:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, amount_item)
            self.table.setItem(row, 3, QTableWidgetItem(expense["currency_code"] or "UZS"))
            self.table.setItem(row, 4, QTableWidgetItem(expense["description"] or ""))
            self.table.setCellWidget(row, 5, self._actions_widget(row))
            self.table.setRowHeight(row, 54)
        set_language(self, self.property("app_language") or "uz")

    def _actions_widget(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        edit_btn = QPushButton("✏ Tahrir")
        delete_btn = QPushButton("🗑 O'chir")
        edit_btn.setFixedSize(92, 30)
        delete_btn.setFixedSize(96, 30)
        edit_btn.setStyleSheet(self._state_button("#fff7ed", "#9a3412", "#fdba74", "#fb923c"))
        delete_btn.setStyleSheet(self._state_button("#fef2f2", "#991b1b", "#fca5a5", "#dc2626"))
        edit_btn.clicked.connect(lambda _, r=row: self._edit_expense(r))
        delete_btn.clicked.connect(lambda _, r=row: self._delete_expense(r))
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        return widget

    def _expense_at_row(self, row):
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _manage_categories(self):
        dlg = CategoryManagerDialog(self)
        dlg.exec()
        self.load_data()

    def _add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            db.add_expense(data["category_id"], data["amount"], data["currency_code"], data["description"])
            self.load_data()

    def _edit_expense(self, row):
        expense = self._expense_at_row(row)
        if not expense:
            return
        dlg = ExpenseDialog(self, expense)
        if dlg.exec():
            data = dlg.get_data()
            db.update_expense(expense["id"], data["category_id"], data["amount"], data["currency_code"], data["description"])
            self.load_data()

    def _delete_expense(self, row):
        expense = self._expense_at_row(row)
        if not expense:
            return
        reply = QMessageBox.question(
            self, "Harajatni o'chirish", "Bu harajat o'chirilsinmi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_expense(expense["id"])
            self.load_data()

    def _show_report(self):
        dlg = ExpenseReportDialog(self)
        dlg.exec()

    def _button_style(self):
        return "background:#3b82f6;color:white;border:none;border-radius:6px;padding:0 14px;font-weight:bold;"

    def _state_button(self, bg, fg, border, hover):
        return f"""
            QPushButton{{background:{bg};color:{fg};border:1px solid {border};border-radius:6px;font-weight:bold;}}
            QPushButton:hover{{background:{hover};color:white;border-color:{hover};}}
            QPushButton:pressed{{background:#1e293b;color:white;border-color:#1e293b;padding-top:2px;}}
        """

    def _table_style(self):
        return """
            QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;}
            QTableWidget::item{padding:7px 10px;}
            QHeaderView::section{background:#f8fafc;border:none;border-bottom:1px solid #e2e8f0;padding:8px;font-weight:bold;color:#64748b;}
            QTableWidget::item:alternate{background:#f8fafc;}
        """
