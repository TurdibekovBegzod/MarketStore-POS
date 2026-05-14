from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
import database as db


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.logged_user = None
        self.setWindowTitle("Market Store POS — Kirish")
        self.setMinimumSize(420, 430)
        self.resize(420, 450)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowTitleHint)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background: #0f172a; }
            QLabel#title { color: #e2e8f0; font-size: 22px; font-weight: bold; }
            QLabel#sub   { color: #64748b; font-size: 13px; }
            QLabel       { color: #cbd5e1; font-size: 13px; }
            QLineEdit {
                background: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 10px 14px;
                color: #e2e8f0; font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            QPushButton#login {
                background: #3b82f6; color: white; font-size: 15px;
                font-weight: bold; border: none; border-radius: 8px;
                padding: 12px;
            }
            QPushButton#login:hover { background: #2563eb; }
            QPushButton#login:pressed { background: #1d4ed8; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 34, 40, 28)
        layout.setSpacing(10)

        icon_lbl = QLabel("🛒")
        icon_lbl.setStyleSheet("font-size: 40px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        title = QLabel("Market Store POS")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Tizimga kirish")
        sub.setObjectName("sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(sub)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Foydalanuvchi nomi")
        self.username_edit.setMinimumHeight(44)
        layout.addWidget(self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Parol")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setMinimumHeight(44)
        self.password_edit.returnPressed.connect(self._try_login)
        layout.addWidget(self.password_edit)

        layout.addSpacing(4)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #f87171; font-size: 12px;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setMinimumHeight(22)
        self.error_lbl.setWordWrap(True)
        layout.addWidget(self.error_lbl)

        btn = QPushButton("Kirish")
        btn.setObjectName("login")
        btn.setMinimumHeight(46)
        btn.clicked.connect(self._try_login)
        layout.addWidget(btn)

        hint = QLabel("Default: admin / admin123")
        hint.setStyleSheet("color: #475569; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    def _try_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()

        if not username or not password:
            self.error_lbl.setText("⚠ Iltimos, barcha maydonlarni to'ldiring")
            return

        user = db.authenticate(username, password)
        if user:
            self.logged_user = dict(user)
            db.log_login(self.logged_user)
            self.accept()
        else:
            self.error_lbl.setText("❌ Noto'g'ri login yoki parol")
            self.password_edit.clear()
            self.password_edit.setFocus()
