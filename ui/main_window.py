from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QMessageBox,
    QDialog, QFormLayout, QComboBox, QLineEdit, QApplication,
    QAbstractButton, QTableWidget, QHeaderView, QSpinBox, QDoubleSpinBox,
    QTextEdit, QDateEdit, QTabWidget, QScrollArea
)
from PyQt6.QtCore import QTimer
from datetime import datetime
import database as db

from ui.sales_widget import SalesWidget
from ui.products_widget import ProductsWidget
from ui.stock_widget import StockWidget
from ui.reports_widget import ReportsWidget
from ui.users_widget import UsersWidget
from ui.login_history_widget import LoginHistoryWidget
from ui.supplier_debts_widget import SupplierDebtsWidget
from ui.expenses_widget import ExpensesWidget
from ui.checking_widget import CheckingWidget
from ui.i18n import set_language


THEMES = {
    "dark_blue": {
        "name": "Dark + Blue",
        "sidebar": "#1a1a2e",
        "sidebar_alt": "#16213e",
        "content": "#f8fafc",
        "topbar": "#ffffff",
        "border": "#2a2a4a",
        "accent": "#3b82f6",
        "nav_text": "#94a3b8",
        "nav_active": "#ffffff",
        "title": "#1e293b",
        "muted": "#64748b",
    },
    "light_blue": {
        "name": "Light + Blue",
        "sidebar": "#eaf2ff",
        "sidebar_alt": "#dbeafe",
        "content": "#f8fbff",
        "topbar": "#ffffff",
        "border": "#bfdbfe",
        "accent": "#2563eb",
        "nav_text": "#1e3a8a",
        "nav_active": "#ffffff",
        "title": "#172554",
        "muted": "#475569",
    },
    "dark_white": {
        "name": "Dark + White",
        "sidebar": "#111827",
        "sidebar_alt": "#1f2937",
        "content": "#f3f4f6",
        "topbar": "#ffffff",
        "border": "#374151",
        "accent": "#f9fafb",
        "nav_text": "#d1d5db",
        "nav_active": "#111827",
        "title": "#111827",
        "muted": "#6b7280",
    },
    "green": {
        "name": "Green + Slate",
        "sidebar": "#0f2f2a",
        "sidebar_alt": "#134e4a",
        "content": "#f0fdf4",
        "topbar": "#ffffff",
        "border": "#2dd4bf",
        "accent": "#10b981",
        "nav_text": "#a7f3d0",
        "nav_active": "#ffffff",
        "title": "#064e3b",
        "muted": "#475569",
    },
}


TEXTS = {
    "uz": {
        "settings": "Sozlamalar", "theme": "Interfeys rangi", "language": "Til",
        "app_name": "Dastur nomi", "save": "Saqlash", "cancel": "Bekor",
        "logout": "Chiqish", "logout_q": "Haqiqatan chiqmoqchimisiz?",
        "Admin": "Admin", "Kassir": "Kassir", "sales": "Sotuv",
        "products": "Mahsulotlar", "stock": "Ombor",
        "reports": "Hisobotlar", "supplier_debts": "Qarzlar", "expenses": "Harajatlar",
        "checking": "Tekshiruv",
        "users": "Kassirlar", "login_history": "Kirish tarixi",
    },
    "en": {
        "settings": "Settings", "theme": "Interface theme", "language": "Language",
        "app_name": "App name", "save": "Save", "cancel": "Cancel",
        "logout": "Logout", "logout_q": "Do you really want to log out?",
        "Admin": "Admin", "Kassir": "Cashier", "sales": "Sales",
        "products": "Products", "stock": "Stock",
        "reports": "Reports", "supplier_debts": "Debts", "expenses": "Expenses",
        "checking": "Checking",
        "users": "Cashiers", "login_history": "Login history",
    },
    "ru": {
        "checking": "Проверка",
        "settings": "Настройки", "theme": "Тема интерфейса", "language": "Язык",
        "app_name": "Название программы", "save": "Сохранить", "cancel": "Отмена",
        "logout": "Выход", "logout_q": "Вы действительно хотите выйти?",
        "Admin": "Админ", "Kassir": "Кассир", "sales": "Продажи",
        "products": "Товары", "stock": "Склад",
        "reports": "Отчеты", "supplier_debts": "Долги", "expenses": "Расходы",
        "users": "Кассиры", "login_history": "История входа",
    },
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None, user_role="cashier", settings=None):
        super().__init__(parent)
        self.user_role = user_role
        self.settings = settings or db.get_app_settings()
        self.setWindowTitle(TEXTS.get(self.settings["language"], TEXTS["uz"])["settings"])
        self.setFixedWidth(420)
        self._build_ui()

    def _build_ui(self):
        labels = TEXTS.get(self.settings["language"], TEXTS["uz"])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        form = QFormLayout()
        self.theme_combo = QComboBox()
        for key, theme in THEMES.items():
            self.theme_combo.addItem(theme["name"], key)
        idx = self.theme_combo.findData(self.settings.get("theme", "dark_blue"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.language_combo = QComboBox()
        self.language_combo.addItem("O'zbek", "uz")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        idx = self.language_combo.findData(self.settings.get("language", "uz"))
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)
        form.addRow(labels["theme"] + ":", self.theme_combo)
        form.addRow(labels["language"] + ":", self.language_combo)
        self.app_name_edit = None
        if self.user_role == "admin":
            self.app_name_edit = QLineEdit(self.settings.get("app_name", "Market POS"))
            form.addRow(labels["app_name"] + ":", self.app_name_edit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        cancel_btn = QPushButton(labels["cancel"])
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton(labels["save"])
        save_btn.setStyleSheet("background:#3b82f6;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:bold;")
        save_btn.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)

    def get_data(self):
        data = {
            "theme": self.theme_combo.currentData(),
            "language": self.language_combo.currentData(),
        }
        if self.app_name_edit is not None:
            data["app_name"] = self.app_name_edit.text().strip() or "Market POS"
        return data


class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.settings = db.get_app_settings(self.user["id"])
        self.labels = TEXTS.get(self.settings["language"], TEXTS["uz"])
        self.setWindowTitle(self.settings["app_name"])
        self.setMinimumSize(1280, 780)
        self._build_ui()
        self._start_clock()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        self.logo_frame = QFrame()
        self.logo_frame.setFixedHeight(70)
        logo_lay = QVBoxLayout(self.logo_frame)
        self.logo_lbl = QLabel(self.settings["app_name"])
        logo_lay.addWidget(self.logo_lbl)
        sb_layout.addWidget(self.logo_frame)

        self.nav_buttons = {}
        nav_frame = QWidget()
        nav_frame.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 16, 12, 0)
        nav_layout.setSpacing(4)

        nav_items = [(self.labels["sales"], "sales")]
        if self.user["role"] == "admin":
            nav_items.extend([
                (self.labels["products"], "products"),
                (self.labels["stock"], "stock"),
                (self.labels["reports"], "reports"),
                (self.labels["supplier_debts"], "supplier_debts"),
                (self.labels["expenses"], "expenses"),
                (self.labels.get("checking", "Checking"), "checking"),
                (self.labels["users"], "users"),
                (self.labels["login_history"], "login_history"),
            ])

        for label, key in nav_items:
            btn = QPushButton(f"  {label}")
            btn.setFixedHeight(46)
            btn.setCheckable(True)
            btn.setObjectName(f"nav_{key}")
            btn.setStyleSheet(self._nav_btn_style())
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        nav_layout.addStretch()
        sb_layout.addWidget(nav_frame)

        self.user_frame = QFrame()
        self.user_frame.setFixedHeight(110)
        user_lay = QVBoxLayout(self.user_frame)
        user_lay.setContentsMargins(16, 10, 16, 12)
        user_lay.setSpacing(5)

        self.uname = QLabel(self.user["username"].capitalize())
        role_row = QHBoxLayout()
        self.urole = QLabel(self.labels["Admin"] if self.user["role"] == "admin" else self.labels["Kassir"])
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(38, 34)
        self.settings_btn.setToolTip(self.labels["settings"])
        self.settings_btn.clicked.connect(self._open_settings)
        role_row.addWidget(self.urole)
        role_row.addStretch()
        role_row.addWidget(self.settings_btn)

        self.logout_btn = QPushButton(self.labels["logout"])
        self.logout_btn.setFixedHeight(28)
        self.logout_btn.clicked.connect(self._logout)
        user_lay.addWidget(self.uname)
        user_lay.addLayout(role_row)
        user_lay.addWidget(self.logout_btn)
        sb_layout.addWidget(self.user_frame)

        root.addWidget(self.sidebar)

        self.content_area = QWidget()
        self.content_area.setObjectName("content")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.topbar = QFrame()
        self.topbar.setFixedHeight(54)
        topbar_lay = QHBoxLayout(self.topbar)
        topbar_lay.setContentsMargins(24, 0, 24, 0)

        self.page_title_lbl = QLabel(self.labels["sales"])
        self.clock_lbl = QLabel()
        topbar_lay.addWidget(self.page_title_lbl)
        topbar_lay.addStretch()
        topbar_lay.addWidget(self.clock_lbl)
        content_layout.addWidget(self.topbar)

        self.stack = QStackedWidget()
        self.pages = {"sales": SalesWidget(self.user)}
        if self.user["role"] == "admin":
            self.pages.update({
                "products": ProductsWidget(self.user),
                "stock": StockWidget(),
                "reports": ReportsWidget(),
                "supplier_debts": SupplierDebtsWidget(),
                "expenses": ExpensesWidget(),
                "checking": CheckingWidget(self.user),
                "users": UsersWidget(),
                "login_history": LoginHistoryWidget(),
            })
        for widget in self.pages.values():
            self.stack.addWidget(widget)
            set_language(widget, self.settings.get("language", "uz"))
        content_layout.addWidget(self.stack)
        root.addWidget(self.content_area)

        self._apply_theme()
        self._switch_page("sales")

    def _nav_btn_style(self):
        theme = THEMES.get(self.settings.get("theme"), THEMES["dark_blue"])
        return """
            QPushButton {
                text-align: left;
                padding-left: 14px;
                font-size: 14px;
                color: %s;
                background: transparent;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.12);
                color: %s;
            }
            QPushButton:checked {
                background: %s;
                color: %s;
                font-weight: bold;
            }
        """ % (theme["nav_text"], theme["nav_text"], theme["accent"], theme["nav_active"])

    def _switch_page(self, key):
        if key not in self.pages:
            key = "sales"
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        self.stack.setCurrentWidget(self.pages[key])
        self.page_title_lbl.setText(self.labels.get(key, key))

        page = self.pages[key]
        if hasattr(page, "load_data"):
            page.load_data()
        set_language(page, self.settings.get("language", "uz"))
        self._apply_page_theme()

    def _start_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(self._update_clock)
        timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
        self.clock_lbl.setText(now)

    def _open_settings(self):
        dlg = SettingsDialog(self, self.user["role"], self.settings)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_data()
            if self.user["role"] != "admin":
                updated.pop("app_name", None)
            db.save_app_settings(updated, self.user["id"])
            self.settings = db.get_app_settings(self.user["id"])
            self.labels = TEXTS.get(self.settings["language"], TEXTS["uz"])
            self._refresh_texts()
            self._apply_theme()

    def _refresh_texts(self):
        self.setWindowTitle(self.settings["app_name"])
        self.logo_lbl.setText(self.settings["app_name"])
        self.urole.setText(self.labels["Admin"] if self.user["role"] == "admin" else self.labels["Kassir"])
        self.logout_btn.setText(self.labels["logout"])
        self.settings_btn.setToolTip(self.labels["settings"])
        for key, btn in self.nav_buttons.items():
            btn.setText(f"  {self.labels.get(key, key)}")
            btn.setStyleSheet(self._nav_btn_style())
        current_key = next((key for key, page in self.pages.items() if page is self.stack.currentWidget()), "sales")
        self.page_title_lbl.setText(self.labels.get(current_key, current_key))
        for page in self.pages.values():
            if hasattr(page, "load_data"):
                page.load_data()
            set_language(page, self.settings.get("language", "uz"))

    def _apply_theme(self):
        theme = THEMES.get(self.settings.get("theme"), THEMES["dark_blue"])
        self.sidebar.setStyleSheet(f"""
            #sidebar {{
                background: {theme['sidebar']};
                border-right: 1px solid {theme['border']};
            }}
        """)
        self.logo_frame.setStyleSheet(f"background:{theme['sidebar_alt']};border-bottom:1px solid {theme['border']};")
        self.logo_lbl.setStyleSheet(f"color:{theme['nav_text']};font-size:18px;font-weight:bold;padding-left:16px;")
        self.user_frame.setStyleSheet(f"background:{theme['sidebar_alt']};border-top:1px solid {theme['border']};")
        self.uname.setStyleSheet(f"color:{theme['nav_text']};font-size:13px;")
        self.urole.setStyleSheet(f"color:{theme['muted']};font-size:11px;")
        self.settings_btn.setStyleSheet(f"""
            QPushButton{{background:transparent;color:{theme['nav_text']};border:1px solid {theme['border']};border-radius:6px;font-family:"Arial Unicode MS","Segoe UI Symbol","Segoe UI";font-size:20px;font-weight:400;padding:0;margin:0;line-height:34px;}}
            QPushButton:hover{{background:{theme['accent']};color:{theme['nav_active']};border-color:{theme['accent']};}}
            QPushButton:pressed{{background:{theme['border']};color:{theme['nav_text']};padding-top:1px;}}
        """)
        self.logout_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #f87171; border: 1px solid #f87171;
                          border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background: #f87171; color: white; }
        """)
        self.content_area.setStyleSheet(f"#content {{ background: {theme['content']}; }}")
        self.topbar.setStyleSheet(f"background:{theme['topbar']};border-bottom:1px solid #e2e8f0;")
        self.page_title_lbl.setStyleSheet(f"font-size:18px;font-weight:bold;color:{theme['title']};")
        self.clock_lbl.setStyleSheet(f"color:{theme['muted']};font-size:13px;")
        for btn in self.nav_buttons.values():
            btn.setStyleSheet(self._nav_btn_style())
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self._global_theme_style(theme))
        self._apply_page_theme()

    def _apply_page_theme(self):
        theme = THEMES.get(self.settings.get("theme"), THEMES["dark_blue"])
        current_page = self.stack.currentWidget()
        if hasattr(current_page, "apply_theme"):
            current_page.apply_theme(theme)
            return
        for widget in self.stack.findChildren(QWidget):
            if current_page and isinstance(current_page, SalesWidget) and current_page.isAncestorOf(widget):
                continue
            if isinstance(widget, QAbstractButton) and self._inside_table(widget):
                continue
            if isinstance(widget, (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit)):
                widget.setStyleSheet(self._field_style(theme))
            elif isinstance(widget, QTableWidget):
                widget.setStyleSheet(self._table_style(theme))
                widget.horizontalHeader().setStyleSheet(self._header_style(theme))
            elif isinstance(widget, QHeaderView):
                widget.setStyleSheet(self._header_style(theme))
            elif isinstance(widget, QTabWidget):
                widget.setStyleSheet(self._tab_style(theme))
            elif isinstance(widget, QAbstractButton):
                widget.setStyleSheet(self._button_style(theme))
            elif isinstance(widget, QFrame):
                widget.setStyleSheet(self._panel_style(theme))
            elif isinstance(widget, QScrollArea):
                widget.setStyleSheet(f"QScrollArea {{ background: {theme['content']}; border: none; }}")
            elif isinstance(widget, QLabel):
                widget.setStyleSheet(self._label_style(theme))
        if isinstance(current_page, SalesWidget):
            self._apply_sales_theme(current_page, theme)

    def _inside_table(self, widget):
        parent = widget.parent()
        while parent is not None:
            if isinstance(parent, QTableWidget):
                return True
            parent = parent.parent()
        return False

    def _apply_sales_theme(self, page, theme):
        page.setStyleSheet(f"background:{theme['content']};")
        for table in page.findChildren(QTableWidget):
            table.setStyleSheet(self._table_style(theme))
            table.horizontalHeader().setStyleSheet(self._header_style(theme))
        for field in page.findChildren((QLineEdit, QComboBox)):
            field.setStyleSheet(self._field_style(theme))
        page.discount_spin.setStyleSheet(self._field_style(theme))
        page.discount_spin.setMinimumHeight(40)
        page.discount_spin.setMinimumWidth(190)
        complete_btn = page.findChild(QPushButton, "complete_sale_btn")
        if complete_btn:
            complete_btn.setFixedHeight(48)
            complete_btn.setStyleSheet("""
                QPushButton {
                    background:#059669; color:white; font-size:15px;
                    font-weight:bold; border:none; border-radius:8px;
                }
                QPushButton:hover { background:#047857; }
                QPushButton:pressed { background:#065f46; padding-top:3px; }
            """)
        clear_btn = page.findChild(QPushButton, "clear_cart_btn")
        if clear_btn:
            clear_btn.setFixedHeight(36)
            clear_btn.setStyleSheet("""
                QPushButton {
                    background:transparent; color:#ef4444; font-size:13px;
                    border:1px solid #ef4444; border-radius:6px;
                }
                QPushButton:hover { background:#ef4444; color:white; }
                QPushButton:pressed { background:#991b1b; color:white; padding-top:3px; }
            """)
        for button in page.products_table.findChildren(QPushButton):
            if button.toolTip() == "Savatga qo'shish" or button.text().strip() == "+":
                button.setFixedSize(25, 25)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background:{theme['accent']}; color:{theme['nav_active']};
                        border:none; border-radius:6px; padding:0;
                        font-size:15px; font-weight:bold;
                    }}
                    QPushButton:hover {{ background:{theme['sidebar_alt']}; color:{theme['nav_text']}; }}
                    QPushButton:pressed {{
                        background:#1d4ed8;
                        color:white;
                        padding-top:2px;
                    }}
                    QPushButton:disabled {{ background:#cbd5e1; color:#64748b; }}
                """)
        for spinner in page.cart_table.findChildren(QSpinBox):
            spinner.setMinimumHeight(34)
            spinner.setStyleSheet(f"""
                QSpinBox {{
                    background:{theme['topbar']}; color:{theme['title']};
                    border:1px solid #cbd5e1; border-radius:6px;
                    padding:3px 8px; font-size:12px; font-weight:600;
                }}
                QSpinBox:focus {{ border-color:{theme['accent']}; }}
                QSpinBox::up-button, QSpinBox::down-button {{ width:20px; }}
            """)
        for button in page.cart_table.findChildren(QPushButton):
            if button.text().strip() in {"✕", "x", "X"}:
                button.setFixedSize(30, 30)
                button.setStyleSheet("""
                    QPushButton {
                        background:#fee2e2; color:#ef4444; border:none;
                        border-radius:6px; font-weight:bold; font-size:13px;
                    }
                    QPushButton:hover { background:#ef4444; color:white; }
                    QPushButton:pressed {
                        background:#991b1b;
                        color:white;
                        padding-top:3px;
                    }
                """)

    def _field_style(self, theme):
        return f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{
                background: {theme['topbar']};
                color: {theme['title']};
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QDateEdit:focus {{
                border-color: {theme['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 22px;
            }}
        """

    def _button_style(self, theme):
        return f"""
            QPushButton {{
                background: {theme['topbar']};
                color: {theme['title']};
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {theme['accent']};
                color: {theme['nav_active']};
                border-color: {theme['accent']};
            }}
            QPushButton:pressed {{
                background: {theme['sidebar_alt']};
                color: {theme['nav_text']};
                padding-top: 7px;
            }}
            QPushButton:checked {{
                background: {theme['accent']};
                color: {theme['nav_active']};
                border-color: {theme['accent']};
            }}
            QPushButton:disabled {{
                background: #e2e8f0;
                color: #94a3b8;
                border-color: #cbd5e1;
            }}
        """

    def _table_style(self, theme):
        return f"""
            QTableWidget {{
                background: {theme['topbar']};
                color: {theme['title']};
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                alternate-background-color: {theme['content']};
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 7px 10px;
            }}
            QTableWidget::item:selected {{
                background: {theme['accent']};
                color: {theme['nav_active']};
            }}
        """

    def _header_style(self, theme):
        return f"""
            QHeaderView::section {{
                background: {theme['content']};
                color: {theme['muted']};
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }}
        """

    def _panel_style(self, theme):
        return f"""
            QFrame {{
                background: {theme['topbar']};
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }}
        """

    def _label_style(self, theme):
        return f"""
            QLabel {{
                color: {theme['title']};
                background: transparent;
                border: none;
            }}
        """

    def _tab_style(self, theme):
        return f"""
            QTabWidget::pane {{
                border: 1px solid #e2e8f0;
                background: {theme['content']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {theme['topbar']};
                color: {theme['muted']};
                border: 1px solid #cbd5e1;
                padding: 8px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {theme['accent']};
                color: {theme['nav_active']};
                border-color: {theme['accent']};
            }}
        """

    def _global_theme_style(self, theme):
        return f"""
            QWidget {{
                font-family: "Segoe UI";
                color: {theme['title']};
                selection-background-color: {theme['accent']};
            }}
            QMainWindow, QStackedWidget, QWidget#content {{
                background: {theme['content']};
            }}
            QDialog {{
                background: {theme['topbar']};
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {theme['topbar']};
                color: {theme['title']};
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 10px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {theme['accent']};
            }}
            QTableWidget {{
                background: {theme['topbar']};
                color: {theme['title']};
                alternate-background-color: {theme['content']};
                gridline-color: #e2e8f0;
            }}
            QHeaderView::section {{
                background: {theme['content']};
                color: {theme['muted']};
                border: none;
                border-bottom: 1px solid #e2e8f0;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton {{
                background: {theme['topbar']};
                color: {theme['title']};
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                border-color: {theme['accent']};
                color: {theme['accent']};
            }}
            QTabWidget::pane {{
                border: 1px solid #e2e8f0;
                background: {theme['content']};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: {theme['topbar']};
                color: {theme['muted']};
                border: 1px solid #cbd5e1;
                padding: 8px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {theme['accent']};
                color: {theme['nav_active']};
                border-color: {theme['accent']};
            }}
            QScrollBar:vertical {{
                border: none; background: #f1f5f9; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #cbd5e1; border-radius: 4px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {theme['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QToolTip {{
                background: #1e293b; color: white; border: none;
                padding: 4px 8px; border-radius: 4px;
            }}
        """

    def _logout(self):
        reply = QMessageBox.question(
            self, self.labels["logout"], self.labels["logout_q"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            from ui.login_dialog import LoginDialog
            dlg = LoginDialog()
            if dlg.exec():
                self.next_window = MainWindow(dlg.logged_user)
                self.next_window.showMaximized()
