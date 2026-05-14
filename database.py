import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

DB_PATH = "market_pos.db"


class AppError(Exception):
    """User-facing application error."""


def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def _verify_password(password, stored_password):
    if not stored_password:
        return False
    if not stored_password.startswith("pbkdf2_sha256$"):
        return secrets.compare_digest(password, stored_password)
    try:
        _, salt, digest = stored_password.split("$", 2)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_password(password, salt), stored_password)

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _raise_database_busy(exc):
    if "locked" in str(exc).lower():
        raise AppError(
            "Ma'lumotlar bazasi hozir band. Dasturning boshqa ochiq oynasi bo'lsa yoping va qayta urinib ko'ring."
        ) from exc
    raise exc


def get_app_settings(user_id=None):
    defaults = {
        "app_name": "Market POS",
        "theme": "dark_blue",
        "language": "uz",
    }
    conn = get_connection()
    try:
        global_rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        user_rows = []
        if user_id is not None:
            user_rows = conn.execute(
                "SELECT key, value FROM user_settings WHERE user_id = ?",
                (user_id,)
            ).fetchall()
    except sqlite3.Error:
        global_rows = []
        user_rows = []
    conn.close()
    settings = dict(defaults)
    settings.update({row["key"]: row["value"] for row in global_rows if row["value"] is not None})
    settings.update({
        row["key"]: row["value"]
        for row in user_rows
        if row["value"] is not None and row["key"] in {"theme", "language"}
    })
    return settings


def save_app_settings(settings, user_id=None):
    allowed = {"app_name", "theme", "language"}
    conn = get_connection()
    try:
        for key, value in settings.items():
            if key not in allowed:
                continue
            if key == "app_name" or user_id is None:
                conn.execute("""
                    INSERT INTO app_settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (key, str(value)))
            else:
                conn.execute("""
                    INSERT INTO user_settings (user_id, key, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value
                """, (user_id, key, str(value)))
        conn.commit()
    finally:
        conn.close()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("PRAGMA journal_mode = WAL")
    except sqlite3.Error:
        pass

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'cashier',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS currencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            rate_to_uzs REAL NOT NULL DEFAULT 1,
            is_base INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (user_id, key)
        );

        CREATE TABLE IF NOT EXISTS product_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_template_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL REFERENCES product_templates(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            field_type TEXT DEFAULT 'text',
            required INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT NOT NULL,
            template_id INTEGER REFERENCES product_templates(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            category_id INTEGER REFERENCES categories(id),
            price REAL NOT NULL DEFAULT 0,
            cost REAL NOT NULL DEFAULT 0,
            price_currency TEXT DEFAULT 'UZS',
            price_exchange_rate REAL DEFAULT 1,
            price_original REAL DEFAULT 0,
            cost_currency TEXT DEFAULT 'UZS',
            cost_exchange_rate REAL DEFAULT 1,
            cost_original REAL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            unit TEXT DEFAULT 'dona',
            process_status TEXT DEFAULT 'available',
            process_quantity INTEGER DEFAULT 0,
            process_deposit REAL DEFAULT 0,
            process_deposit_currency TEXT DEFAULT 'UZS',
            is_deleted INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_attributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            field_id INTEGER NOT NULL REFERENCES product_template_fields(id) ON DELETE CASCADE,
            value TEXT,
            UNIQUE(product_id, field_id)
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            balance REAL DEFAULT 0,
            total_purchases REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            note TEXT,
            debt_currency TEXT DEFAULT 'UZS',
            balance REAL DEFAULT 0,
            total_received REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS supplier_debt_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS debtors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            note TEXT,
            debt_currency TEXT DEFAULT 'UZS',
            balance REAL DEFAULT 0,
            total_given REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS debtor_debt_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debtor_id INTEGER NOT NULL REFERENCES debtors(id),
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER REFERENCES expense_categories(id),
            amount REAL NOT NULL,
            currency_code TEXT DEFAULT 'UZS',
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id),
            cashier_id INTEGER REFERENCES users(id),
            customer_name TEXT,
            customer_phone TEXT,
            total REAL NOT NULL,
            discount REAL DEFAULT 0,
            paid REAL NOT NULL,
            change REAL DEFAULT 0,
            currency_code TEXT DEFAULT 'UZS',
            exchange_rate REAL DEFAULT 1,
            paid_original REAL DEFAULT 0,
            change_original REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'naqd',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER REFERENCES sales(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            returned_quantity INTEGER DEFAULT 0,
            price REAL NOT NULL,
            subtotal REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER REFERENCES products(id),
            type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS inventory_check_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_by INTEGER REFERENCES users(id),
            status TEXT NOT NULL DEFAULT 'active',
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        );

        CREATE TABLE IF NOT EXISTS inventory_check_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES inventory_check_sessions(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id),
            product_name TEXT NOT NULL,
            barcode TEXT,
            expected_stock INTEGER DEFAULT 0,
            checked_quantity INTEGER DEFAULT 0,
            checked_at TEXT,
            UNIQUE(session_id, product_id)
        );
    """)

    columns = [row["name"] for row in c.execute("PRAGMA table_info(products)").fetchall()]
    if "template_id" not in columns:
        c.execute("ALTER TABLE products ADD COLUMN template_id INTEGER REFERENCES product_templates(id)")
    columns = [row["name"] for row in c.execute("PRAGMA table_info(products)").fetchall()]
    if "supplier_id" not in columns:
        c.execute("ALTER TABLE products ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id)")
    product_migrations = {
        "price_currency": "ALTER TABLE products ADD COLUMN price_currency TEXT DEFAULT 'UZS'",
        "price_exchange_rate": "ALTER TABLE products ADD COLUMN price_exchange_rate REAL DEFAULT 1",
        "price_original": "ALTER TABLE products ADD COLUMN price_original REAL DEFAULT 0",
        "cost_currency": "ALTER TABLE products ADD COLUMN cost_currency TEXT DEFAULT 'UZS'",
        "cost_exchange_rate": "ALTER TABLE products ADD COLUMN cost_exchange_rate REAL DEFAULT 1",
        "cost_original": "ALTER TABLE products ADD COLUMN cost_original REAL DEFAULT 0",
        "process_status": "ALTER TABLE products ADD COLUMN process_status TEXT DEFAULT 'available'",
        "process_quantity": "ALTER TABLE products ADD COLUMN process_quantity INTEGER DEFAULT 0",
        "process_deposit": "ALTER TABLE products ADD COLUMN process_deposit REAL DEFAULT 0",
        "process_deposit_currency": "ALTER TABLE products ADD COLUMN process_deposit_currency TEXT DEFAULT 'UZS'",
        "is_deleted": "ALTER TABLE products ADD COLUMN is_deleted INTEGER DEFAULT 0",
    }
    columns = [row["name"] for row in c.execute("PRAGMA table_info(products)").fetchall()]
    for column, sql in product_migrations.items():
        if column not in columns:
            c.execute(sql)
    columns = [row["name"] for row in c.execute("PRAGMA table_info(products)").fetchall()]
    if "min_stock" in columns:
        try:
            c.execute("ALTER TABLE products DROP COLUMN min_stock")
        except sqlite3.OperationalError:
            pass

    sale_columns = [row["name"] for row in c.execute("PRAGMA table_info(sales)").fetchall()]
    sale_migrations = {
        "customer_name": "ALTER TABLE sales ADD COLUMN customer_name TEXT",
        "customer_phone": "ALTER TABLE sales ADD COLUMN customer_phone TEXT",
        "currency_code": "ALTER TABLE sales ADD COLUMN currency_code TEXT DEFAULT 'UZS'",
        "exchange_rate": "ALTER TABLE sales ADD COLUMN exchange_rate REAL DEFAULT 1",
        "paid_original": "ALTER TABLE sales ADD COLUMN paid_original REAL DEFAULT 0",
        "change_original": "ALTER TABLE sales ADD COLUMN change_original REAL DEFAULT 0",
    }
    for column, sql in sale_migrations.items():
        if column not in sale_columns:
            try:
                c.execute(sql)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

    sale_item_columns = [row["name"] for row in c.execute("PRAGMA table_info(sale_items)").fetchall()]
    if "returned_quantity" not in sale_item_columns:
        c.execute("ALTER TABLE sale_items ADD COLUMN returned_quantity INTEGER DEFAULT 0")

    supplier_columns = [row["name"] for row in c.execute("PRAGMA table_info(suppliers)").fetchall()]
    if "debt_currency" not in supplier_columns:
        c.execute("ALTER TABLE suppliers ADD COLUMN debt_currency TEXT DEFAULT 'UZS'")

    check_item_columns = [row["name"] for row in c.execute("PRAGMA table_info(inventory_check_items)").fetchall()]
    if "checked_quantity" not in check_item_columns:
        c.execute("ALTER TABLE inventory_check_items ADD COLUMN checked_quantity INTEGER DEFAULT 0")

    # Default admin user
    c.execute("SELECT id, password FROM users WHERE username = ?", ("admin",))
    admin = c.fetchone()
    if admin is None:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("admin", _hash_password("admin123"), "admin"))
    elif not str(admin["password"]).startswith("pbkdf2_sha256$"):
        c.execute("UPDATE users SET password = ? WHERE id = ?",
                  (_hash_password(admin["password"]), admin["id"]))

    has_global_name = c.execute("SELECT value FROM app_settings WHERE key = 'app_name'").fetchone()
    if has_global_name is None:
        old_name = c.execute("""
            SELECT us.value
            FROM user_settings us
            LEFT JOIN users u ON u.id = us.user_id
            WHERE us.key = 'app_name' AND us.value IS NOT NULL AND TRIM(us.value) <> ''
            ORDER BY CASE WHEN u.role = 'admin' THEN 0 ELSE 1 END, us.user_id
            LIMIT 1
        """).fetchone()
        if old_name:
            c.execute("INSERT INTO app_settings (key, value) VALUES ('app_name', ?)", (old_name["value"],))

    # Sample categories
    for cat in ["Oziq-ovqat", "Ichimliklar", "Gigiena", "Uy-ro'zg'or"]:
        try:
            c.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        except sqlite3.IntegrityError:
            pass

    # Default currencies. Rates can be edited from the app.
    for code, name, rate, is_base in [
        ("UZS", "O'zbek so'mi", 1, 1),
        ("USD", "AQSh dollari", 12500, 0),
        ("EUR", "Yevro", 13500, 0),
    ]:
        try:
            c.execute("""
                INSERT INTO currencies (code, name, rate_to_uzs, is_base)
                VALUES (?, ?, ?, ?)
            """, (code, name, rate, is_base))
        except sqlite3.IntegrityError:
            pass

    for cat in ["Ijara", "Transport", "Kommunal", "Ish haqi", "Boshqa"]:
        try:
            c.execute("INSERT INTO expense_categories (name) VALUES (?)", (cat,))
        except sqlite3.IntegrityError:
            pass

    # Sample templates
    if c.execute("SELECT COUNT(*) FROM product_templates").fetchone()[0] == 0:
        c.execute("INSERT INTO product_templates (name) VALUES (?)", ("Umumiy mahsulot",))
        template_id = c.lastrowid
        for order, field_name in enumerate(["Brend", "Model", "Rang"]):
            c.execute("""
                INSERT INTO product_template_fields (template_id, name, sort_order)
                VALUES (?, ?, ?)
            """, (template_id, field_name, order))

    conn.commit()
    conn.close()


# ── Products ──────────────────────────────────────────────
def get_all_products():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*, c.name as category_name, t.name as template_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_templates t ON p.template_id = t.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE COALESCE(p.is_deleted, 0) = 0
        ORDER BY p.name
    """).fetchall()
    conn.close()
    return rows

def search_products(query):
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.*, c.name as category_name, t.name as template_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_templates t ON p.template_id = t.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE COALESCE(p.is_deleted, 0) = 0 AND (p.name LIKE ? OR p.barcode LIKE ?)
        ORDER BY p.name
    """, (f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return rows

def get_product_by_barcode(barcode):
    conn = get_connection()
    row = conn.execute("""
        SELECT p.*, c.name as category_name, t.name as template_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_templates t ON p.template_id = t.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.barcode=? AND COALESCE(p.is_deleted, 0) = 0
    """, (barcode,)).fetchone()
    conn.close()
    return row

def add_product(data: dict):
    data = _normalize_product_money(data)
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO products (
            barcode, name, template_id, supplier_id, category_id, price, cost,
            price_currency, price_exchange_rate, price_original,
            cost_currency, cost_exchange_rate, cost_original,
            stock, unit
        )
        VALUES (
            :barcode, :name, :template_id, :supplier_id, :category_id, :price, :cost,
            :price_currency, :price_exchange_rate, :price_original,
            :cost_currency, :cost_exchange_rate, :cost_original,
            :stock, :unit
        )
    """, data)
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id

def update_product(product_id, data: dict):
    data = _normalize_product_money(data)
    conn = get_connection()
    conn.execute("""
        UPDATE products SET barcode=:barcode, name=:name, template_id=:template_id,
        supplier_id=:supplier_id, category_id=:category_id,
        price=:price, cost=:cost,
        price_currency=:price_currency, price_exchange_rate=:price_exchange_rate, price_original=:price_original,
        cost_currency=:cost_currency, cost_exchange_rate=:cost_exchange_rate, cost_original=:cost_original,
        stock=:stock, unit=:unit
        WHERE id=:id
    """, {**data, "id": product_id})
    conn.commit()
    conn.close()


def _normalize_product_money(data):
    normalized = dict(data)
    normalized.setdefault("price_currency", "UZS")
    normalized.setdefault("price_exchange_rate", 1)
    normalized.setdefault("price_original", normalized.get("price", 0))
    normalized.setdefault("cost_currency", "UZS")
    normalized.setdefault("cost_exchange_rate", 1)
    normalized.setdefault("cost_original", normalized.get("cost", 0))
    normalized.setdefault("supplier_id", None)
    normalized.setdefault("category_id", None)
    return normalized

def delete_product(product_id):
    conn = get_connection()
    conn.execute("UPDATE products SET is_deleted = 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def set_product_process_status(product_id, status):
    if status not in ("available", "process"):
        raise AppError("Mahsulot holati noto'g'ri.")
    conn = get_connection()
    conn.execute("UPDATE products SET process_status = ? WHERE id = ?", (status, product_id))
    conn.commit()
    conn.close()


def put_product_in_process(product_id, quantity, deposit_amount=0, deposit_currency="UZS"):
    if quantity <= 0:
        raise AppError("Jarayonga o'tkazish miqdori 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    try:
        product = conn.execute("""
            SELECT stock, COALESCE(process_quantity, 0) as process_quantity
            FROM products
            WHERE id = ? AND COALESCE(is_deleted, 0) = 0
        """, (product_id,)).fetchone()
        if not product:
            raise AppError("Mahsulot topilmadi.")
        available = (product["stock"] or 0) - (product["process_quantity"] or 0)
        if quantity > available:
            raise AppError(f"Bor qoldiqdan ko'p kiritildi. Mavjud: {available}.")
        conn.execute("""
            UPDATE products
            SET process_status = 'process',
                process_quantity = COALESCE(process_quantity, 0) + ?,
                process_deposit = COALESCE(process_deposit, 0) + ?,
                process_deposit_currency = ?
            WHERE id = ?
        """, (quantity, deposit_amount, deposit_currency, product_id))
        conn.commit()
    finally:
        conn.close()


def clear_product_process(product_id):
    conn = get_connection()
    conn.execute("""
        UPDATE products
        SET process_status = 'available',
            process_quantity = 0,
            process_deposit = 0,
            process_deposit_currency = 'UZS'
        WHERE id = ?
    """, (product_id,))
    conn.commit()
    conn.close()


def reduce_product_process(product_id, quantity):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT COALESCE(process_quantity, 0) as process_quantity,
                   COALESCE(process_deposit, 0) as process_deposit
            FROM products
            WHERE id = ?
        """, (product_id,)).fetchone()
        if not row:
            raise AppError("Mahsulot topilmadi.")
        current_qty = row["process_quantity"] or 0
        if quantity > current_qty:
            raise AppError(f"Jarayondagi miqdordan ko'p. Jarayonda: {current_qty}.")
        remaining_qty = current_qty - quantity
        remaining_deposit = 0
        if current_qty > 0 and remaining_qty > 0:
            remaining_deposit = (row["process_deposit"] or 0) * remaining_qty / current_qty
        conn.execute("""
            UPDATE products
            SET process_status = CASE WHEN ? > 0 THEN 'process' ELSE 'available' END,
                process_quantity = ?,
                process_deposit = ?,
                process_deposit_currency = CASE WHEN ? > 0 THEN process_deposit_currency ELSE 'UZS' END
            WHERE id = ?
        """, (remaining_qty, remaining_qty, remaining_deposit, remaining_qty, product_id))
        conn.commit()
    finally:
        conn.close()

def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return rows


def add_category(name):
    if not name.strip():
        raise AppError("Kategoriya nomini kiriting.")
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu kategoriya allaqachon mavjud.") from exc
    finally:
        conn.close()


def update_category(category_id, name):
    if not name.strip():
        raise AppError("Kategoriya nomini kiriting.")
    conn = get_connection()
    try:
        conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name.strip(), category_id))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu kategoriya allaqachon mavjud.") from exc
    finally:
        conn.close()


def delete_category(category_id):
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET category_id = NULL WHERE category_id = ?", (category_id,))
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
    finally:
        conn.close()


def get_templates():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM product_templates ORDER BY name").fetchall()
    conn.close()
    return rows


def get_template_fields(template_id):
    if not template_id:
        return []
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM product_template_fields
        WHERE template_id = ?
        ORDER BY sort_order, id
    """, (template_id,)).fetchall()
    conn.close()
    return rows


def add_template(name, fields):
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO product_templates (name) VALUES (?)", (name,))
        template_id = cursor.lastrowid
        for order, field in enumerate(fields):
            conn.execute("""
                INSERT INTO product_template_fields (template_id, name, field_type, required, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (template_id, field["name"], field.get("field_type", "text"), int(field.get("required", False)), order))
        conn.commit()
        return template_id
    finally:
        conn.close()


def update_template(template_id, name, fields):
    conn = get_connection()
    try:
        conn.execute("UPDATE product_templates SET name = ? WHERE id = ?", (name, template_id))
        existing_rows = conn.execute("""
            SELECT id, name FROM product_template_fields
            WHERE template_id = ?
        """, (template_id,)).fetchall()
        existing_by_name = {row["name"].lower(): row["id"] for row in existing_rows}
        kept_ids = []
        for order, field in enumerate(fields):
            field_id = existing_by_name.get(field["name"].lower())
            if field_id:
                conn.execute("""
                    UPDATE product_template_fields
                    SET field_type = ?, required = ?, sort_order = ?
                    WHERE id = ?
                """, (field.get("field_type", "text"), int(field.get("required", False)), order, field_id))
                kept_ids.append(field_id)
            else:
                cursor = conn.execute("""
                    INSERT INTO product_template_fields (template_id, name, field_type, required, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (template_id, field["name"], field.get("field_type", "text"), int(field.get("required", False)), order))
                kept_ids.append(cursor.lastrowid)
        if kept_ids:
            placeholders = ",".join("?" for _ in kept_ids)
            conn.execute(
                f"DELETE FROM product_template_fields WHERE template_id = ? AND id NOT IN ({placeholders})",
                [template_id, *kept_ids]
            )
        else:
            conn.execute("DELETE FROM product_template_fields WHERE template_id = ?", (template_id,))
        conn.commit()
    finally:
        conn.close()


def delete_template(template_id):
    conn = get_connection()
    try:
        in_use = conn.execute("SELECT COUNT(*) FROM products WHERE template_id = ?", (template_id,)).fetchone()[0]
        if in_use:
            raise AppError("Bu template mahsulotlarda ishlatilgan, uni o'chirib bo'lmaydi.")
        conn.execute("DELETE FROM product_templates WHERE id = ?", (template_id,))
        conn.commit()
    finally:
        conn.close()


def get_product_attributes(product_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT pa.field_id, pa.value, ptf.name
        FROM product_attributes pa
        JOIN product_template_fields ptf ON ptf.id = pa.field_id
        WHERE pa.product_id = ?
        ORDER BY ptf.sort_order, ptf.id
    """, (product_id,)).fetchall()
    conn.close()
    return {row["field_id"]: row["value"] for row in rows}


def save_product_attributes(product_id, attributes):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM product_attributes WHERE product_id = ?", (product_id,))
        for field_id, value in attributes.items():
            if value is None or str(value).strip() == "":
                continue
            conn.execute("""
                INSERT INTO product_attributes (product_id, field_id, value)
                VALUES (?, ?, ?)
            """, (product_id, field_id, str(value).strip()))
        conn.commit()
    finally:
        conn.close()


# ── Currencies ────────────────────────────────────────────
def get_currencies():
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM currencies
        ORDER BY is_base DESC, code
    """).fetchall()
    conn.close()
    return rows


def get_currency(code):
    conn = get_connection()
    row = conn.execute("SELECT * FROM currencies WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row


def save_currency(code, name, rate_to_uzs):
    code = code.strip().upper()
    name = name.strip()
    if not code or not name:
        raise AppError("Valyuta kodi va nomini kiriting.")
    if rate_to_uzs <= 0:
        raise AppError("Kurs 0 dan katta bo'lishi kerak.")

    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO currencies (code, name, rate_to_uzs, is_base, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                rate_to_uzs = excluded.rate_to_uzs,
                updated_at = CURRENT_TIMESTAMP
        """, (code, name, rate_to_uzs, 1 if code == "UZS" else 0))
        conn.commit()
    finally:
        conn.close()


def delete_currency(code):
    if code == "UZS":
        raise AppError("Asosiy valyutani o'chirib bo'lmaydi.")
    conn = get_connection()
    try:
        conn.execute("DELETE FROM currencies WHERE code = ?", (code,))
        conn.commit()
    finally:
        conn.close()


# ── Sales ─────────────────────────────────────────────────
def add_stock(product_id, quantity, note=""):
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity, product_id))
        conn.execute("""
            INSERT INTO stock_movements (product_id, type, quantity, note)
            VALUES (?, ?, ?, ?)
        """, (product_id, "kirim", quantity, note))
        conn.commit()
    finally:
        conn.close()


# Inventory checking
def get_active_inventory_check():
    conn = get_connection()
    row = conn.execute("""
        SELECT s.*, u.username as started_by_name
        FROM inventory_check_sessions s
        LEFT JOIN users u ON u.id = s.started_by
        WHERE s.status = 'active'
        ORDER BY s.started_at DESC, s.id DESC
        LIMIT 1
    """).fetchone()
    conn.close()
    return row


def start_inventory_check(user_id=None):
    conn = get_connection()
    try:
        active = conn.execute("""
            SELECT id FROM inventory_check_sessions
            WHERE status = 'active'
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()
        if active:
            raise AppError("Oldin boshlangan checking jarayoni bor. Avval uni tugating.")

        cursor = conn.execute(
            "INSERT INTO inventory_check_sessions (started_by, status) VALUES (?, 'active')",
            (user_id,)
        )
        session_id = cursor.lastrowid
        products = conn.execute("""
            SELECT id, name, barcode, stock
            FROM products
            WHERE COALESCE(is_deleted, 0) = 0 AND COALESCE(stock, 0) > 0
            ORDER BY name
        """).fetchall()
        for product in products:
            conn.execute("""
                INSERT INTO inventory_check_items (
                    session_id, product_id, product_name, barcode, expected_stock
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                product["id"],
                product["name"],
                product["barcode"],
                product["stock"] or 0,
            ))
        conn.commit()
        return session_id
    finally:
        conn.close()


def get_inventory_check_items(session_id, checked=None):
    conn = get_connection()
    condition = ""
    if checked is True:
        condition = "AND COALESCE(checked_quantity, 0) > 0"
    elif checked is False:
        condition = "AND COALESCE(checked_quantity, 0) < COALESCE(expected_stock, 0)"
    rows = conn.execute(f"""
        SELECT *
        FROM inventory_check_items
        WHERE session_id = ?
        {condition}
        ORDER BY CASE WHEN checked_at IS NULL THEN 0 ELSE 1 END, product_name
    """, (session_id,)).fetchall()
    conn.close()
    return rows


def get_inventory_check_counts(session_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN checked_at IS NOT NULL THEN 1 ELSE 0 END) as checked_count,
            SUM(CASE WHEN COALESCE(checked_quantity, 0) < COALESCE(expected_stock, 0) THEN 1 ELSE 0 END) as unchecked_count,
            SUM(COALESCE(expected_stock, 0)) as total_quantity,
            SUM(COALESCE(checked_quantity, 0)) as checked_quantity,
            SUM(CASE
                WHEN COALESCE(expected_stock, 0) > COALESCE(checked_quantity, 0)
                THEN COALESCE(expected_stock, 0) - COALESCE(checked_quantity, 0)
                ELSE 0
            END) as unchecked_quantity
        FROM inventory_check_items
        WHERE session_id = ?
    """, (session_id,)).fetchone()
    conn.close()
    return row


def mark_inventory_product_checked(session_id, barcode, quantity=1):
    barcode = (barcode or "").strip()
    if not barcode:
        raise AppError("Shtrix-kodni kiriting.")
    if quantity <= 0:
        raise AppError("Miqdor 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    try:
        session = conn.execute(
            "SELECT id FROM inventory_check_sessions WHERE id = ? AND status = 'active'",
            (session_id,)
        ).fetchone()
        if not session:
            raise AppError("Aktiv checking jarayoni topilmadi.")

        product = conn.execute("""
            SELECT id, name, barcode
            FROM products
            WHERE barcode = ? AND COALESCE(is_deleted, 0) = 0
        """, (barcode,)).fetchone()
        if not product:
            raise AppError("Bu shtrix-kodli mahsulot topilmadi.")

        item = conn.execute("""
            SELECT *
            FROM inventory_check_items
            WHERE session_id = ? AND product_id = ?
        """, (session_id, product["id"])).fetchone()
        if not item:
            raise AppError("Bu mahsulot checking ro'yxatida yo'q.")
        if item["checked_at"]:
            raise AppError("Bu mahsulot allaqachon tekshiruvdan o'tgan.")
        current_quantity = item["checked_quantity"] or 0
        expected_stock = item["expected_stock"] or 0
        new_quantity = current_quantity + quantity
        if new_quantity > expected_stock:
            raise AppError(f"Kiritilgan miqdor qoldiqdan oshib ketdi. Qolgan: {expected_stock - current_quantity}.")

        if new_quantity == expected_stock:
            conn.execute("""
                UPDATE inventory_check_items
                SET checked_quantity = ?, checked_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_quantity, item["id"]))
        else:
            conn.execute("""
                UPDATE inventory_check_items
                SET checked_quantity = ?
                WHERE id = ?
            """, (new_quantity, item["id"]))
        conn.commit()
        return conn.execute("SELECT * FROM inventory_check_items WHERE id = ?", (item["id"],)).fetchone()
    finally:
        conn.close()


def finish_inventory_check(session_id):
    conn = get_connection()
    try:
        session = conn.execute(
            "SELECT id FROM inventory_check_sessions WHERE id = ? AND status = 'active'",
            (session_id,)
        ).fetchone()
        if not session:
            raise AppError("Aktiv checking jarayoni topilmadi.")
        counts = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN checked_at IS NOT NULL THEN 1 ELSE 0 END) as checked_count,
                SUM(CASE WHEN COALESCE(checked_quantity, 0) < COALESCE(expected_stock, 0) THEN 1 ELSE 0 END) as unchecked_count,
                SUM(COALESCE(expected_stock, 0)) as total_quantity,
                SUM(COALESCE(checked_quantity, 0)) as checked_quantity,
                SUM(CASE
                    WHEN COALESCE(expected_stock, 0) > COALESCE(checked_quantity, 0)
                    THEN COALESCE(expected_stock, 0) - COALESCE(checked_quantity, 0)
                    ELSE 0
                END) as unchecked_quantity
            FROM inventory_check_items
            WHERE session_id = ?
        """, (session_id,)).fetchone()
        conn.execute("""
            UPDATE inventory_check_sessions
            SET status = 'finished', finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session_id,))
        conn.commit()
        return counts
    finally:
        conn.close()


def create_sale(
    customer_id, cashier_id, items, total, discount, paid, payment_method,
    currency_code="UZS", exchange_rate=1, paid_original=None,
    customer_name=None, customer_phone=None
):
    if not items:
        raise AppError("Savat bo'sh.")
    if discount < 0 or discount > total:
        raise AppError("Chegirma jami summadan oshmasligi kerak.")
    if payment_method == "qarz" and not customer_id:
        raise AppError("Qarz savdo uchun mijoz tanlang.")
    if exchange_rate <= 0:
        raise AppError("Valyuta kursi noto'g'ri.")

    conn = get_connection()
    try:
        conn.execute("BEGIN")
        c = conn.cursor()

        for item in items:
            product = c.execute(
                "SELECT id, name, stock, price FROM products WHERE id = ?",
                (item["product_id"],)
            ).fetchone()
            if product is None:
                raise AppError("Savatdagi mahsulot topilmadi.")
            if item["quantity"] <= 0:
                raise AppError("Miqdor noto'g'ri kiritilgan.")
            if product["stock"] < item["quantity"]:
                raise AppError(
                    f"{product['name']} uchun qoldiq yetarli emas. "
                    f"Mavjud: {product['stock']}, so'ralgan: {item['quantity']}."
                )

        payable = total - discount
        change = max(0, paid - payable)
        paid_original = paid_original if paid_original is not None else paid / exchange_rate
        change_original = change / exchange_rate
        if customer_id and (not customer_name or customer_phone is None):
            customer = c.execute("SELECT name, phone FROM customers WHERE id = ?", (customer_id,)).fetchone()
            if customer:
                customer_name = customer_name or customer["name"]
                customer_phone = customer["phone"] if customer_phone is None else customer_phone
        c.execute("""
            INSERT INTO sales (
                customer_id, cashier_id, customer_name, customer_phone, total, discount, paid, change,
                currency_code, exchange_rate, paid_original, change_original, payment_method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id, cashier_id, customer_name, customer_phone, total, discount, paid, change,
            currency_code, exchange_rate, paid_original, change_original, payment_method
        ))
        sale_id = c.lastrowid

        for item in items:
            c.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, item["product_id"], item["quantity"], item["price"], item["subtotal"]))
            c.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                      (item["quantity"], item["product_id"]))
            c.execute("""
                INSERT INTO stock_movements (product_id, type, quantity, note)
                VALUES (?, ?, ?, ?)
            """, (item["product_id"], "sotuv", -item["quantity"], f"Sotuv #{sale_id}"))

        if customer_id:
            if payment_method == "qarz":
                c.execute("""
                    UPDATE customers
                    SET total_purchases = total_purchases + ?, balance = balance + ?
                    WHERE id = ?
                """, (payable, payable, customer_id))
            else:
                c.execute("UPDATE customers SET total_purchases = total_purchases + ? WHERE id = ?",
                          (payable, customer_id))

        conn.commit()
        return sale_id
    except sqlite3.OperationalError as exc:
        conn.rollback()
        _raise_database_busy(exc)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_sales_today():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute("""
        SELECT s.*, u.username as cashier_name, c.name as customer_name
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE DATE(s.created_at) = ?
        ORDER BY s.created_at DESC
    """, (today,)).fetchall()
    conn.close()
    return rows

def get_sale_items(sale_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT si.*, p.name as product_name
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    """, (sale_id,)).fetchall()
    conn.close()
    return rows


def get_product_sales_archive(query=""):
    conn = get_connection()
    pattern = f"%{query.strip()}%"
    params = []
    conditions = ["si.quantity > COALESCE(si.returned_quantity, 0)"]
    if query and query.strip():
        conditions.append("(p.name LIKE ? OR p.barcode LIKE ? OR u.username LIKE ? OR COALESCE(s.customer_name, c.name) LIKE ? OR COALESCE(s.customer_phone, c.phone) LIKE ?)")
        params = [pattern, pattern, pattern, pattern, pattern]
    where = "WHERE " + " AND ".join(conditions)
    rows = conn.execute(f"""
        SELECT
            si.id as sale_item_id,
            si.sale_id,
            si.product_id,
            p.name as product_name,
            p.barcode,
            p.template_id,
            p.supplier_id,
            si.quantity,
            COALESCE(si.returned_quantity, 0) as returned_quantity,
            si.price,
            si.subtotal,
            s.discount,
            s.payment_method,
            s.currency_code,
            s.exchange_rate,
            s.created_at,
            u.username as cashier_name,
            COALESCE(s.customer_name, c.name) as customer_name,
            COALESCE(s.customer_phone, c.phone) as customer_phone
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        JOIN products p ON p.id = si.product_id
        LEFT JOIN users u ON u.id = s.cashier_id
        LEFT JOIN customers c ON c.id = s.customer_id
        {where}
        ORDER BY s.created_at DESC, si.id DESC
        LIMIT 1000
    """, params).fetchall()
    conn.close()
    return rows


def return_sale_item(sale_item_id, quantity, note=""):
    if quantity <= 0:
        raise AppError("Qaytarish miqdori 0 dan katta bo'lishi kerak.")

    conn = get_connection()
    try:
        conn.execute("BEGIN")
        c = conn.cursor()
        row = c.execute("""
            SELECT
                si.id,
                si.sale_id,
                si.product_id,
                si.quantity,
                COALESCE(si.returned_quantity, 0) as returned_quantity,
                si.price,
                s.customer_id,
                s.payment_method,
                s.exchange_rate
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.id = ?
        """, (sale_item_id,)).fetchone()
        if row is None:
            raise AppError("Sotuv arxivi topilmadi.")

        available = row["quantity"] - row["returned_quantity"]
        if quantity > available:
            raise AppError(f"Qaytarish miqdori ko'p. Qaytarish mumkin: {available}.")

        refund = row["price"] * quantity
        rate = row["exchange_rate"] or 1
        c.execute("""
            UPDATE sale_items
            SET returned_quantity = COALESCE(returned_quantity, 0) + ?
            WHERE id = ?
        """, (quantity, sale_item_id))
        c.execute(
            "UPDATE products SET stock = stock + ?, is_deleted = 0 WHERE id = ?",
            (quantity, row["product_id"])
        )
        c.execute("""
            INSERT INTO stock_movements (product_id, type, quantity, note)
            VALUES (?, ?, ?, ?)
        """, (
            row["product_id"],
            "qaytarish",
            quantity,
            note or f"Sotuv #{row['sale_id']} qaytarildi",
        ))
        c.execute("""
            UPDATE sales
            SET total = MAX(total - ?, 0),
                discount = MIN(discount, MAX(total - ?, 0)),
                paid = CASE WHEN payment_method = 'qarz' THEN paid ELSE MAX(paid - ?, 0) END,
                paid_original = CASE
                    WHEN payment_method = 'qarz' THEN paid_original
                    ELSE MAX(paid_original - ?, 0)
                END
            WHERE id = ?
        """, (refund, refund, refund, refund / rate, row["sale_id"]))

        if row["customer_id"]:
            if row["payment_method"] == "qarz":
                c.execute("""
                    UPDATE customers
                    SET balance = MAX(balance - ?, 0),
                        total_purchases = MAX(total_purchases - ?, 0)
                    WHERE id = ?
                """, (refund, refund, row["customer_id"]))
            else:
                c.execute("""
                    UPDATE customers
                    SET total_purchases = MAX(total_purchases - ?, 0)
                    WHERE id = ?
                """, (refund, row["customer_id"]))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sale_cost(sale_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost), 0) as cost
        FROM sale_items si
        JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
    """, (sale_id,)).fetchone()
    conn.close()
    return row["cost"] or 0

def get_daily_report(date_str):
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(CASE WHEN total - discount > 0 THEN 1 ELSE 0 END), 0) as count,
               SUM(total - discount) as revenue,
               SUM(total - discount - (
                   SELECT SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost)
                   FROM sale_items si JOIN products p ON si.product_id = p.id
                   WHERE si.sale_id = s.id
               )) as profit
        FROM sales s
        WHERE DATE(s.created_at) = ?
    """, (date_str,)).fetchone()
    conn.close()
    return row


def get_sales_by_date(date_str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.*, u.username as cashier_name, c.name as customer_name
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        LEFT JOIN customers c ON s.customer_id = c.id
        WHERE DATE(s.created_at) = ?
        ORDER BY s.created_at DESC
    """, (date_str,)).fetchall()
    conn.close()
    return rows


def get_cashier_report(date_str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            u.id as cashier_id,
            u.username as cashier_name,
            COALESCE(SUM(CASE WHEN s.id IS NOT NULL AND s.total - s.discount > 0 THEN 1 ELSE 0 END), 0) as sales_count,
            COALESCE(SUM(s.total - s.discount), 0) as revenue,
            COALESCE(SUM(s.total - s.discount - (
                SELECT COALESCE(SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost), 0)
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = s.id
            )), 0) as profit
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        WHERE DATE(s.created_at) = ?
        GROUP BY u.id, u.username
        ORDER BY revenue DESC
    """, (date_str,)).fetchall()
    conn.close()
    return rows


def get_cashier_sold_items(date_str, cashier_id=None):
    conn = get_connection()
    params = [date_str]
    cashier_filter = ""
    if cashier_id:
        cashier_filter = "AND s.cashier_id = ?"
        params.append(cashier_id)
    rows = conn.execute(f"""
        SELECT
            p.name as product_name,
            p.barcode,
            SUM(si.quantity - COALESCE(si.returned_quantity, 0)) as quantity,
            si.price,
            SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * si.price) as revenue,
            SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost) as cost,
            SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * (si.price - p.cost)) as profit
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        JOIN products p ON p.id = si.product_id
        WHERE DATE(s.created_at) = ?
        {cashier_filter}
        GROUP BY p.id, p.name, p.barcode, si.price
        ORDER BY revenue DESC
    """, params).fetchall()
    conn.close()
    return rows


def get_overall_period_series(start_date, end_date):
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            DATE(s.created_at) as label,
            COALESCE(SUM(CASE WHEN s.total - s.discount > 0 THEN 1 ELSE 0 END), 0) as sales_count,
            COALESCE(SUM((
                SELECT COALESCE(SUM(si.quantity - COALESCE(si.returned_quantity, 0)), 0)
                FROM sale_items si
                WHERE si.sale_id = s.id
            )), 0) as product_count,
            COALESCE(SUM(s.total - s.discount), 0) as revenue,
            COALESCE(SUM(s.total - s.discount - (
                SELECT COALESCE(SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost), 0)
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = s.id
            )), 0) as profit
        FROM sales s
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        GROUP BY DATE(s.created_at)
        ORDER BY DATE(s.created_at)
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_cashier_period_summary(start_date, end_date):
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            u.id as entity_id,
            u.username as entity_name,
            COALESCE(SUM(CASE WHEN s.id IS NOT NULL AND s.total - s.discount > 0 THEN 1 ELSE 0 END), 0) as sales_count,
            COALESCE(SUM(CASE WHEN s.id IS NOT NULL THEN (
                SELECT COALESCE(SUM(si.quantity - COALESCE(si.returned_quantity, 0)), 0)
                FROM sale_items si
                WHERE si.sale_id = s.id
            ) ELSE 0 END), 0) as product_count,
            COALESCE(SUM(s.total - s.discount), 0) as revenue,
            COALESCE(SUM(s.total - s.discount - (
                SELECT COALESCE(SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost), 0)
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = s.id
            )), 0) as profit
        FROM users u
        LEFT JOIN sales s ON s.cashier_id = u.id AND DATE(s.created_at) BETWEEN ? AND ?
        GROUP BY u.id, u.username
        ORDER BY revenue DESC, u.username
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_customer_period_summary(start_date, end_date):
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            c.id as entity_id,
            c.name as entity_name,
            COALESCE(SUM(CASE WHEN s.id IS NOT NULL AND s.total - s.discount > 0 THEN 1 ELSE 0 END), 0) as sales_count,
            COALESCE(SUM(CASE WHEN s.id IS NOT NULL THEN (
                SELECT COALESCE(SUM(si.quantity - COALESCE(si.returned_quantity, 0)), 0)
                FROM sale_items si
                WHERE si.sale_id = s.id
            ) ELSE 0 END), 0) as product_count,
            COALESCE(SUM(s.total - s.discount), 0) as revenue,
            COALESCE(SUM(s.total - s.discount - (
                SELECT COALESCE(SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost), 0)
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = s.id
            )), 0) as profit
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id AND DATE(s.created_at) BETWEEN ? AND ?
        GROUP BY c.id, c.name
        ORDER BY revenue DESC, c.name
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_entity_period_series(entity_type, entity_id, start_date, end_date):
    if entity_type not in ("cashier", "customer"):
        raise AppError("Hisobot turi noto'g'ri.")
    column = "cashier_id" if entity_type == "cashier" else "customer_id"
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT
            DATE(s.created_at) as label,
            COALESCE(SUM(CASE WHEN s.total - s.discount > 0 THEN 1 ELSE 0 END), 0) as sales_count,
            COALESCE(SUM((
                SELECT COALESCE(SUM(si.quantity - COALESCE(si.returned_quantity, 0)), 0)
                FROM sale_items si
                WHERE si.sale_id = s.id
            )), 0) as product_count,
            COALESCE(SUM(s.total - s.discount), 0) as revenue,
            COALESCE(SUM(s.total - s.discount - (
                SELECT COALESCE(SUM((si.quantity - COALESCE(si.returned_quantity, 0)) * p.cost), 0)
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = s.id
            )), 0) as profit
        FROM sales s
        WHERE s.{column} = ? AND DATE(s.created_at) BETWEEN ? AND ?
        GROUP BY DATE(s.created_at)
        ORDER BY DATE(s.created_at)
    """, (entity_id, start_date, end_date)).fetchall()
    conn.close()
    return rows


# ── Customers ─────────────────────────────────────────────
def get_all_customers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
    conn.close()
    return rows

def add_customer(name, phone, email):
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)",
                              (name, phone, email))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.OperationalError as exc:
        _raise_database_busy(exc)
    finally:
        conn.close()

def update_customer(cid, name, phone, email):
    conn = get_connection()
    try:
        conn.execute("UPDATE customers SET name=?, phone=?, email=? WHERE id=?",
                     (name, phone, email, cid))
        conn.commit()
    except sqlite3.OperationalError as exc:
        _raise_database_busy(exc)
    finally:
        conn.close()


# ── Suppliers / Purchase Debts ────────────────────────────
def get_all_suppliers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
    conn.close()
    return rows


def add_supplier(name, phone=None, note=None, debt_currency="UZS"):
    if not name.strip():
        raise AppError("Ta'minotchi nomini kiriting.")
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO suppliers (name, phone, note, debt_currency) VALUES (?, ?, ?, ?)",
        (name.strip(), phone, note, debt_currency)
    )
    conn.commit()
    supplier_id = cursor.lastrowid
    conn.close()
    return supplier_id


def update_supplier(supplier_id, name, phone=None, note=None, debt_currency=None):
    if not name.strip():
        raise AppError("Ta'minotchi nomini kiriting.")
    conn = get_connection()
    if debt_currency:
        conn.execute(
            "UPDATE suppliers SET name=?, phone=?, note=?, debt_currency=? WHERE id=?",
            (name.strip(), phone, note, debt_currency, supplier_id)
        )
    else:
        conn.execute(
            "UPDATE suppliers SET name=?, phone=?, note=? WHERE id=?",
            (name.strip(), phone, note, supplier_id)
        )
    conn.commit()
    conn.close()


def delete_supplier(supplier_id):
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET supplier_id = NULL WHERE supplier_id = ?", (supplier_id,))
        conn.execute("DELETE FROM supplier_debt_movements WHERE supplier_id = ?", (supplier_id,))
        conn.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        conn.commit()
    finally:
        conn.close()


def add_supplier_debt(supplier_id, amount, note=""):
    if amount <= 0:
        raise AppError("Qarz summasi 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    conn.execute("UPDATE suppliers SET balance = balance + ?, total_received = total_received + ? WHERE id = ?",
                 (amount, amount, supplier_id))
    conn.execute("""
        INSERT INTO supplier_debt_movements (supplier_id, type, amount, note)
        VALUES (?, ?, ?, ?)
    """, (supplier_id, "qarz", amount, note))
    conn.commit()
    conn.close()


def pay_supplier_debt(supplier_id, amount, note=""):
    if amount <= 0:
        raise AppError("To'lov summasi 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    conn.execute("UPDATE suppliers SET balance = MAX(balance - ?, 0) WHERE id = ?",
                 (amount, supplier_id))
    conn.execute("""
        INSERT INTO supplier_debt_movements (supplier_id, type, amount, note)
        VALUES (?, ?, ?, ?)
    """, (supplier_id, "tolov", amount, note))
    conn.commit()
    conn.close()


def get_supplier_debt_movements(supplier_id=None):
    conn = get_connection()
    if supplier_id:
        rows = conn.execute("""
            SELECT m.*, s.name as supplier_name
            FROM supplier_debt_movements m
            JOIN suppliers s ON s.id = m.supplier_id
            WHERE supplier_id = ?
            ORDER BY m.created_at DESC, m.id DESC
        """, (supplier_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.*, s.name as supplier_name
            FROM supplier_debt_movements m
            JOIN suppliers s ON s.id = m.supplier_id
            ORDER BY m.created_at DESC, m.id DESC
        """).fetchall()
    conn.close()
    return rows


# ── Given debts ───────────────────────────────────────────
def get_all_debtors():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM debtors ORDER BY name").fetchall()
    conn.close()
    return rows


def add_debtor(name, phone=None, note=None, debt_currency="UZS"):
    if not name.strip():
        raise AppError("Qarz oluvchi nomini kiriting.")
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO debtors (name, phone, note, debt_currency) VALUES (?, ?, ?, ?)",
        (name.strip(), phone, note, debt_currency)
    )
    conn.commit()
    debtor_id = cursor.lastrowid
    conn.close()
    return debtor_id


def update_debtor(debtor_id, name, phone=None, note=None, debt_currency=None):
    if not name.strip():
        raise AppError("Qarz oluvchi nomini kiriting.")
    conn = get_connection()
    if debt_currency:
        conn.execute(
            "UPDATE debtors SET name=?, phone=?, note=?, debt_currency=? WHERE id=?",
            (name.strip(), phone, note, debt_currency, debtor_id)
        )
    else:
        conn.execute(
            "UPDATE debtors SET name=?, phone=?, note=? WHERE id=?",
            (name.strip(), phone, note, debtor_id)
        )
    conn.commit()
    conn.close()


def delete_debtor(debtor_id):
    conn = get_connection()
    conn.execute("DELETE FROM debtor_debt_movements WHERE debtor_id = ?", (debtor_id,))
    conn.execute("DELETE FROM debtors WHERE id = ?", (debtor_id,))
    conn.commit()
    conn.close()


def add_debtor_debt(debtor_id, amount, note=""):
    if amount <= 0:
        raise AppError("Qarz summasi 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    conn.execute("UPDATE debtors SET balance = balance + ?, total_given = total_given + ? WHERE id = ?",
                 (amount, amount, debtor_id))
    conn.execute("""
        INSERT INTO debtor_debt_movements (debtor_id, type, amount, note)
        VALUES (?, ?, ?, ?)
    """, (debtor_id, "qarz", amount, note))
    conn.commit()
    conn.close()


def pay_debtor_debt(debtor_id, amount, note=""):
    if amount <= 0:
        raise AppError("To'lov summasi 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    conn.execute("UPDATE debtors SET balance = MAX(balance - ?, 0) WHERE id = ?",
                 (amount, debtor_id))
    conn.execute("""
        INSERT INTO debtor_debt_movements (debtor_id, type, amount, note)
        VALUES (?, ?, ?, ?)
    """, (debtor_id, "tolov", amount, note))
    conn.commit()
    conn.close()


def get_debtor_debt_movements(debtor_id=None):
    conn = get_connection()
    if debtor_id:
        rows = conn.execute("""
            SELECT m.*, d.name as debtor_name
            FROM debtor_debt_movements m
            JOIN debtors d ON d.id = m.debtor_id
            WHERE debtor_id = ?
            ORDER BY m.created_at DESC, m.id DESC
        """, (debtor_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.*, d.name as debtor_name
            FROM debtor_debt_movements m
            JOIN debtors d ON d.id = m.debtor_id
            ORDER BY m.created_at DESC, m.id DESC
        """).fetchall()
    conn.close()
    return rows


# ── Expenses ──────────────────────────────────────────────
def get_expense_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM expense_categories ORDER BY name").fetchall()
    conn.close()
    return rows


def add_expense_category(name):
    if not name.strip():
        raise AppError("Kategoriya nomini kiriting.")
    conn = get_connection()
    try:
        cursor = conn.execute("INSERT INTO expense_categories (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu kategoriya allaqachon mavjud.") from exc
    finally:
        conn.close()


def update_expense_category(category_id, name):
    if not name.strip():
        raise AppError("Kategoriya nomini kiriting.")
    conn = get_connection()
    try:
        conn.execute("UPDATE expense_categories SET name = ? WHERE id = ?", (name.strip(), category_id))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu kategoriya allaqachon mavjud.") from exc
    finally:
        conn.close()


def delete_expense_category(category_id):
    conn = get_connection()
    conn.execute("UPDATE expenses SET category_id = NULL WHERE category_id = ?", (category_id,))
    conn.execute("DELETE FROM expense_categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


def get_expenses():
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.*, c.name as category_name
        FROM expenses e
        LEFT JOIN expense_categories c ON c.id = e.category_id
        ORDER BY e.created_at DESC, e.id DESC
    """).fetchall()
    conn.close()
    return rows


def add_expense(category_id, amount, currency_code, description):
    if amount <= 0:
        raise AppError("Harajat summasi 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO expenses (category_id, amount, currency_code, description)
        VALUES (?, ?, ?, ?)
    """, (category_id, amount, currency_code, description))
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def update_expense(expense_id, category_id, amount, currency_code, description):
    if amount <= 0:
        raise AppError("Harajat summasi 0 dan katta bo'lishi kerak.")
    conn = get_connection()
    conn.execute("""
        UPDATE expenses
        SET category_id = ?, amount = ?, currency_code = ?, description = ?
        WHERE id = ?
    """, (category_id, amount, currency_code, description, expense_id))
    conn.commit()
    conn.close()


def delete_expense(expense_id):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def get_expense_report(start_date, end_date, category_id=None):
    conn = get_connection()
    params = [start_date, end_date]
    category_filter = ""
    if category_id:
        category_filter = "AND category_id = ?"
        params.append(category_id)
    rows = conn.execute(f"""
        SELECT DATE(created_at) as label, currency_code, COALESCE(SUM(amount), 0) as amount
        FROM expenses
        WHERE DATE(created_at) BETWEEN ? AND ?
        {category_filter}
        GROUP BY DATE(created_at), currency_code
        ORDER BY DATE(created_at)
    """, params).fetchall()
    conn.close()
    return rows


def get_expense_category_report(start_date, end_date, category_id=None):
    conn = get_connection()
    params = [start_date, end_date]
    category_filter = ""
    if category_id:
        category_filter = "AND e.category_id = ?"
        params.append(category_id)
    rows = conn.execute(f"""
        SELECT COALESCE(c.name, 'Kategoriya yo''q') as category_name,
               e.currency_code,
               COALESCE(SUM(e.amount), 0) as amount
        FROM expenses e
        LEFT JOIN expense_categories c ON c.id = e.category_id
        WHERE DATE(e.created_at) BETWEEN ? AND ?
        {category_filter}
        GROUP BY c.name, e.currency_code
        ORDER BY amount DESC
    """, params).fetchall()
    conn.close()
    return rows


# ── Auth ──────────────────────────────────────────────────
def authenticate(username, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    if row and _verify_password(password, row["password"]):
        if not str(row["password"]).startswith("pbkdf2_sha256$"):
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (_hash_password(password), row["id"]))
            conn.commit()
        conn.close()
        return row
    conn.close()
    return None


def log_login(user):
    conn = get_connection()
    conn.execute("""
        INSERT INTO login_logs (user_id, username, role)
        VALUES (?, ?, ?)
    """, (user["id"], user["username"], user["role"]))
    conn.commit()
    conn.close()


def get_login_logs(limit=500):
    conn = get_connection()
    rows = conn.execute("""
        SELECT *
        FROM login_logs
        ORDER BY logged_at DESC, id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def clear_login_logs():
    conn = get_connection()
    conn.execute("DELETE FROM login_logs")
    conn.commit()
    conn.close()


# ── Users ─────────────────────────────────────────────────
def get_users():
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, username, role, created_at
        FROM users
        ORDER BY role, username
    """).fetchall()
    conn.close()
    return rows


def add_user(username, password, role="cashier"):
    username = username.strip()
    if not username or not password:
        raise AppError("Username va parol kiriting.")
    if role not in ("admin", "cashier"):
        raise AppError("Role noto'g'ri.")
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, _hash_password(password), role)
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu username allaqachon mavjud.") from exc
    finally:
        conn.close()


def update_user(user_id, username, password=None, role="cashier"):
    username = username.strip()
    if not username:
        raise AppError("Username kiriting.")
    if role not in ("admin", "cashier"):
        raise AppError("Role noto'g'ri.")
    conn = get_connection()
    try:
        if password:
            conn.execute("""
                UPDATE users SET username = ?, password = ?, role = ?
                WHERE id = ?
            """, (username, _hash_password(password), role, user_id))
        else:
            conn.execute("UPDATE users SET username = ?, role = ? WHERE id = ?",
                         (username, role, user_id))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu username allaqachon mavjud.") from exc
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    try:
        admins = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if user and user["role"] == "admin" and admins <= 1:
            raise AppError("Oxirgi adminni o'chirib bo'lmaydi.")
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AppError("Bu foydalanuvchi sotuv tarixida bor, uni o'chirib bo'lmaydi.") from exc
    finally:
        conn.close()

def get_low_stock_products():
    return []
