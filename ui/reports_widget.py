from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox,
    QGridLayout, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
import database as db
from ui.i18n import set_language


class LineChart(QWidget):
    def __init__(self, title="Grafik", color="#3b82f6"):
        super().__init__()
        self.title = title
        self.color = color
        self.points = []
        self.setMinimumHeight(190)
        self.setStyleSheet("background:white;border:1px solid #e2e8f0;border-radius:8px;")

    def set_data(self, points):
        self.points = points
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(16, 14, -16, -14)
        painter.setPen(QColor("#334155"))
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

        values = [value for _, value in self.points]
        max_value = max(values) or 1
        count = max(len(self.points) - 1, 1)
        plotted = []
        for index, (_, value) in enumerate(self.points):
            x = chart.left() + (index / count) * chart.width()
            y = chart.bottom() - (value / max_value) * chart.height()
            plotted.append(QPointF(x, y))

        painter.setPen(QPen(QColor(self.color), 3))
        for index in range(1, len(plotted)):
            painter.drawLine(plotted[index - 1], plotted[index])

        painter.setBrush(QColor(self.color))
        painter.setPen(QPen(QColor("#ffffff"), 2))
        for point in plotted:
            painter.drawEllipse(point, 4, 4)

        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(chart.left() - 40, chart.top() + 8, f"{max_value:,.0f}")
        painter.drawText(chart.left() - 22, chart.bottom(), "0")
        painter.drawText(chart.left(), chart.bottom() + 20, self.points[0][0])
        painter.drawText(chart.right() - 70, chart.bottom() + 20, self.points[-1][0])


class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.detail_mode = "overall"
        self.detail_metric = "revenue"
        self.selected_entity_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Sana:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setFixedWidth(210)
        self.date_edit.setFixedHeight(36)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                border:1px solid #d1d5db;
                border-radius:6px;
                padding:0 10px;
                background:white;
                font-size:13px;
            }
            QDateEdit::drop-down { width:28px; border:none; }
        """)
        self.date_edit.dateChanged.connect(self.load_data)
        toolbar.addWidget(self.date_edit)

        self.period_combo = QComboBox()
        self.period_combo.addItem("Haftalik", "week")
        self.period_combo.addItem("Oylik", "month")
        self.period_combo.setStyleSheet("border:1px solid #d1d5db;border-radius:6px;padding:6px 10px;background:white;")
        self.period_combo.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.period_combo)

        today_btn = QPushButton("Bugun")
        today_btn.setStyleSheet("background:#3b82f6;color:white;border:none;border-radius:6px;padding:7px 16px;")
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        toolbar.addWidget(today_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.summary_layout = QGridLayout()
        self.summary_layout.setSpacing(12)
        self.summary_cards = {}
        for index, (key, title, color) in enumerate([
            ("revenue", "Daromad", "#059669"),
            ("profit", "Foyda", "#8b5cf6"),
            ("count", "Sotuvlar soni", "#3b82f6"),
            ("products", "Mahsulotlar soni", "#0ea5e9"),
            ("avg", "O'rtacha chek", "#f59e0b"),
        ]):
            card = QFrame()
            card.setObjectName(f"summary_{key}")
            card.setProperty("accent_color", color)
            card.setFixedHeight(72)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setStyleSheet(f"""
                QFrame#summary_{key} {{
                    background:white;
                    border-left:4px solid {color};
                    border-top:1px solid #e2e8f0;
                    border-right:1px solid #e2e8f0;
                    border-bottom:1px solid #e2e8f0;
                    border-radius:8px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 8, 14, 8)
            card_layout.setSpacing(4)
            title_lbl = QLabel(title)
            title_lbl.setObjectName("summary_title")
            title_lbl.setStyleSheet("color:#64748b;font-size:11px;")
            value_lbl = QLabel("0")
            value_lbl.setObjectName("summary_value")
            value_lbl.setProperty("accent_color", color)
            value_lbl.setStyleSheet(f"color:{color};font-size:14px;font-weight:bold;")
            value_lbl.setWordWrap(False)
            value_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card_layout.addWidget(title_lbl)
            card_layout.addWidget(value_lbl)
            card_layout.addStretch()
            self.summary_cards[key] = value_lbl
            self.summary_layout.addWidget(card, 0, index)
        layout.addLayout(self.summary_layout)

        detail_header = QHBoxLayout()
        report_title = QLabel("Hisobot turi:")
        report_title.setStyleSheet("font-size:14px;font-weight:bold;color:#1e293b;")
        detail_header.addWidget(report_title)
        self.overall_btn = self._mode_button("Umumiy", "overall")
        self.cashier_btn = self._mode_button("Kassirlar hisoboti", "cashier")
        detail_header.addWidget(self.overall_btn)
        detail_header.addWidget(self.cashier_btn)
        detail_header.addStretch()
        layout.addLayout(detail_header)

        metric_row = QHBoxLayout()
        metric_row.setContentsMargins(0, 0, 0, 0)
        metric_row.setSpacing(8)
        metric_label = QLabel("Grafik:")
        metric_label.setStyleSheet("color:#64748b;font-size:12px;font-weight:bold;")
        metric_row.addWidget(metric_label)
        for key, label in [
            ("revenue", "Daromad"),
            ("profit", "Foyda"),
            ("count", "Cheklar"),
            ("products", "Mahsulotlar"),
            ("avg", "O'rtacha chek"),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setMinimumWidth(86)
            btn.setMaximumWidth(128)
            btn.setStyleSheet(self._toggle_style())
            btn.clicked.connect(lambda checked, metric=key: self._set_detail_metric(metric))
            setattr(self, f"metric_{key}_btn", btn)
            metric_row.addWidget(btn)
        metric_row.addStretch()
        layout.addLayout(metric_row)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(12)
        self.entity_panel = QFrame()
        self.entity_panel.setFrameShape(QFrame.Shape.NoFrame)
        entity_layout = QVBoxLayout(self.entity_panel)
        entity_layout.setContentsMargins(0, 0, 0, 0)
        self.entity_table = QTableWidget()
        self.entity_table.setColumnCount(6)
        self.entity_table.setHorizontalHeaderLabels(["Nomi", "Cheklar", "Mahsulot", "Daromad", "Foyda", "O'rtacha"])
        self.entity_table.setMinimumWidth(570)
        self.entity_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.entity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        for column in range(1, 6):
            self.entity_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        self.entity_table.setColumnWidth(0, 160)
        self.entity_table.setColumnWidth(1, 58)
        self.entity_table.setColumnWidth(2, 74)
        self.entity_table.setColumnWidth(3, 90)
        self.entity_table.setColumnWidth(4, 90)
        self.entity_table.setColumnWidth(5, 90)
        self.entity_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.entity_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.entity_table.setAlternatingRowColors(True)
        self.entity_table.setMaximumHeight(220)
        self.entity_table.setStyleSheet(self._table_style())
        self.entity_table.itemSelectionChanged.connect(self._on_entity_selected)
        entity_layout.addWidget(self.entity_table)
        detail_row.addWidget(self.entity_panel, 4)

        self.detail_chart = LineChart("Tanlangan hisobot grafigi", "#3b82f6")
        self.detail_chart.setMinimumHeight(220)
        detail_row.addWidget(self.detail_chart, 5)
        layout.addLayout(detail_row, 1)

        self.overall_rows = []
        self._sync_buttons()
        self.load_data()

    def apply_theme(self, theme):
        self.setStyleSheet(f"background:{theme['content']};")
        field_style = f"""
            QDateEdit, QComboBox {{
                background:{theme['topbar']};
                color:{theme['title']};
                border:1px solid #cbd5e1;
                border-radius:6px;
                padding:0 10px;
                font-size:13px;
            }}
            QDateEdit:focus, QComboBox:focus {{ border-color:{theme['accent']}; }}
            QDateEdit::drop-down, QComboBox::drop-down {{
                border:none;
                width:28px;
            }}
        """
        self.date_edit.setFixedWidth(210)
        self.date_edit.setFixedHeight(36)
        self.date_edit.setStyleSheet(field_style)
        self.period_combo.setMinimumHeight(38)
        self.period_combo.setStyleSheet(field_style)

        for card in self.findChildren(QFrame):
            if card.objectName().startswith("summary_"):
                color = card.property("accent_color") or theme["accent"]
                card.setStyleSheet(f"""
                    QFrame#{card.objectName()} {{
                        background:{theme['topbar']};
                        border-left:4px solid {color};
                        border-top:1px solid #e2e8f0;
                        border-right:1px solid #e2e8f0;
                        border-bottom:1px solid #e2e8f0;
                        border-radius:8px;
                    }}
                """)
        for label in self.findChildren(QLabel):
            if label.objectName() == "summary_title":
                label.setStyleSheet(f"color:{theme['muted']};font-size:11px;background:transparent;border:none;")
            elif label.objectName() == "summary_value":
                color = label.property("accent_color") or theme["accent"]
                label.setStyleSheet(f"color:{color};font-size:14px;font-weight:bold;background:transparent;border:none;")
            else:
                label.setStyleSheet(f"color:{theme['title']};background:transparent;border:none;")

        button_style = self._toggle_style(theme)
        for button in [
            self.overall_btn,
            self.cashier_btn,
            self.metric_revenue_btn,
            self.metric_profit_btn,
            self.metric_count_btn,
            self.metric_products_btn,
            self.metric_avg_btn,
        ]:
            button.setStyleSheet(button_style)

        for button in self.findChildren(QPushButton):
            if button.text() == "Bugun":
                button.setMinimumHeight(38)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background:{theme['accent']};
                        color:{theme['nav_active']};
                        border:none;
                        border-radius:6px;
                        padding:7px 16px;
                        font-weight:bold;
                    }}
                    QPushButton:hover {{ background:{theme['sidebar_alt']}; color:{theme['nav_text']}; }}
                    QPushButton:pressed {{ background:#1d4ed8; padding-top:9px; }}
                """)
        self.entity_table.setStyleSheet(self._table_style(theme))

    def load_data(self):
        start_date, end_date = self._date_range()
        rows = db.get_overall_period_series(start_date, end_date)
        filled = self._filled_series(rows, start_date, end_date)

        totals = {
            "revenue": sum(row["revenue"] for row in filled),
            "profit": sum(row["profit"] for row in filled),
            "count": sum(row["sales_count"] for row in filled),
            "products": sum(row["product_count"] for row in filled),
        }
        totals["avg"] = totals["revenue"] / totals["count"] if totals["count"] else 0
        self.summary_cards["revenue"].setText(f"{totals['revenue']:,.0f} so'm")
        self.summary_cards["profit"].setText(f"{totals['profit']:,.0f} so'm")
        self.summary_cards["count"].setText(f"{totals['count']:,.0f}")
        self.summary_cards["products"].setText(f"{totals['products']:,.0f}")
        self.summary_cards["avg"].setText(f"{totals['avg']:,.0f} so'm")

        self.overall_rows = filled
        self._refresh_report_panel(start_date, end_date, filled)
        set_language(self, self.property("app_language") or "uz")

    def _refresh_report_panel(self, start_date, end_date, overall_rows):
        if self.detail_mode == "overall":
            self.selected_entity_id = None
            self.entity_panel.hide()
            titles = {
                "revenue": "Umumiy daromad",
                "profit": "Umumiy foyda",
                "count": "Umumiy cheklar",
                "products": "Umumiy sotilgan mahsulotlar",
                "avg": "Umumiy o'rtacha chek",
            }
            self.detail_chart.title = titles[self.detail_metric]
            self._set_chart_data(self.detail_chart, overall_rows, self.detail_metric)
            return

        self.entity_panel.show()
        self._load_entities(start_date, end_date)

    def _load_entities(self, start_date, end_date):
        current = self.selected_entity_id
        rows = db.get_cashier_period_summary(start_date, end_date)
        title = "Kassirlar hisoboti"
        self.detail_chart.title = title
        self.entity_table.blockSignals(True)
        self.entity_table.setRowCount(0)
        selected_row = 0 if rows else -1
        for row, item in enumerate(rows):
            self.entity_table.insertRow(row)
            name = item["entity_name"] or "Noma'lum"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, item["entity_id"])
            self.entity_table.setItem(row, 0, name_item)
            self.entity_table.setItem(row, 1, QTableWidgetItem(str(item["sales_count"] or 0)))
            self.entity_table.setItem(row, 2, QTableWidgetItem(str(item["product_count"] or 0)))
            revenue = item["revenue"] or 0
            profit = item["profit"] or 0
            avg = revenue / item["sales_count"] if item["sales_count"] else 0
            self.entity_table.setItem(row, 3, self._money_item(revenue))
            self.entity_table.setItem(row, 4, self._money_item(profit))
            self.entity_table.setItem(row, 5, self._money_item(avg))
            if current == item["entity_id"]:
                selected_row = row
        self.entity_table.blockSignals(False)
        if selected_row >= 0:
            self.entity_table.selectRow(selected_row)
        else:
            self.selected_entity_id = None
            self.detail_chart.set_data([])

    def _on_entity_selected(self):
        row = self.entity_table.currentRow()
        item = self.entity_table.item(row, 0) if row >= 0 else None
        self.selected_entity_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        self._refresh_detail_chart()

    def _refresh_detail_chart(self):
        if not self.selected_entity_id:
            self.detail_chart.set_data([])
            return
        start_date, end_date = self._date_range()
        rows = db.get_entity_period_series(self.detail_mode, self.selected_entity_id, start_date, end_date)
        filled = self._filled_series(rows, start_date, end_date)
        label = self.entity_table.item(self.entity_table.currentRow(), 0).text()
        titles = {
            "revenue": "daromad",
            "profit": "foyda",
            "count": "cheklar",
            "products": "mahsulotlar",
            "avg": "o'rtacha chek",
        }
        self.detail_chart.title = f"{label}: {titles[self.detail_metric]}"
        self._set_chart_data(self.detail_chart, filled, self.detail_metric)

    def _set_chart_data(self, chart, rows, metric):
        points = []
        for row in rows:
            if metric == "avg":
                value = row["revenue"] / row["sales_count"] if row["sales_count"] else 0
            elif metric == "count":
                value = row["sales_count"]
            elif metric == "products":
                value = row["product_count"]
            else:
                value = row[metric]
            points.append((row["label"][5:], value))
        chart.set_data(points)

    def _date_range(self):
        selected = self.date_edit.date().toPyDate()
        if self.period_combo.currentData() == "month":
            start = selected.replace(day=1)
            if selected.month == 12:
                end = selected.replace(year=selected.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = selected.replace(month=selected.month + 1, day=1) - timedelta(days=1)
        else:
            start = selected - timedelta(days=selected.weekday())
            end = start + timedelta(days=6)
        return start.isoformat(), end.isoformat()

    def _filled_series(self, rows, start_date, end_date):
        by_label = {row["label"]: dict(row) for row in rows}
        current = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        filled = []
        while current <= end:
            label = current.isoformat()
            filled.append(by_label.get(label, {
                "label": label,
                "sales_count": 0,
                "product_count": 0,
                "revenue": 0,
                "profit": 0,
            }))
            current += timedelta(days=1)
        return filled

    def _mode_button(self, label, mode):
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setFixedHeight(34)
        btn.setStyleSheet(self._toggle_style())
        btn.clicked.connect(lambda checked: self._set_detail_mode(mode))
        return btn

    def _set_detail_mode(self, mode):
        self.detail_mode = mode
        self.selected_entity_id = None
        self._sync_buttons()
        start_date, end_date = self._date_range()
        self._refresh_report_panel(start_date, end_date, self.overall_rows)

    def _set_detail_metric(self, metric):
        self.detail_metric = metric
        self._sync_buttons()
        if self.detail_mode == "overall":
            start_date, end_date = self._date_range()
            self._refresh_report_panel(start_date, end_date, self.overall_rows)
        else:
            self._refresh_detail_chart()

    def _sync_buttons(self):
        self.overall_btn.setChecked(self.detail_mode == "overall")
        self.cashier_btn.setChecked(self.detail_mode == "cashier")
        for key in ["revenue", "profit", "count", "products", "avg"]:
            getattr(self, f"metric_{key}_btn").setChecked(self.detail_metric == key)

    def _money_item(self, value):
        item = QTableWidgetItem(f"{value:,.0f} so'm")
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item


    def _toggle_style(self, theme=None):
        if theme:
            return f"""
            QPushButton {{ background:{theme['topbar']};color:{theme['title']};border:1px solid #cbd5e1;
                          border-radius:6px;padding:0 12px;font-size:12px;font-weight:bold; }}
            QPushButton:hover {{ background:{theme['content']}; }}
            QPushButton:pressed {{ background:{theme['sidebar_alt']};color:{theme['nav_text']};padding-top:2px; }}
            QPushButton:checked {{ background:{theme['accent']};color:{theme['nav_active']};border-color:{theme['accent']}; }}
        """
        return """
            QPushButton { background:white;color:#334155;border:1px solid #cbd5e1;
                          border-radius:6px;padding:0 12px;font-size:12px;font-weight:bold; }
            QPushButton:hover { background:#f8fafc; }
            QPushButton:pressed { background:#e2e8f0;padding-top:2px; }
            QPushButton:checked { background:#3b82f6;color:white;border-color:#3b82f6; }
        """

    def _table_style(self, theme=None):
        if theme:
            return f"""
            QTableWidget{{background:{theme['topbar']};color:{theme['title']};border:1px solid #e2e8f0;border-radius:8px;font-size:13px;}}
            QTableWidget::item{{padding:7px 10px;}}
            QTableWidget::item:selected{{background:{theme['accent']};color:{theme['nav_active']};}}
            QHeaderView::section{{background:{theme['content']};border:none;border-bottom:1px solid #e2e8f0;padding:8px;font-weight:bold;color:{theme['muted']};}}
            QTableWidget::item:alternate{{background:{theme['content']};}}
        """
        return """
            QTableWidget{background:white;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;}
            QTableWidget::item{padding:7px 10px;}
            QHeaderView::section{background:#f8fafc;border:none;border-bottom:1px solid #e2e8f0;padding:8px;font-weight:bold;color:#64748b;}
            QTableWidget::item:alternate{background:#f8fafc;}
        """
