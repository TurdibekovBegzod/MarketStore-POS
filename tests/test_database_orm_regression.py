import os
import tempfile
import unittest
from datetime import datetime

import database as db


class DatabaseOrmRegressionTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.old_path = db.DB_PATH
        db.DB_PATH = self.path
        db.init_db()

    def tearDown(self):
        try:
            db._get_engine().dispose()
        finally:
            db.DB_PATH = self.old_path
            for suffix in ("", "-shm", "-wal"):
                path = self.path + suffix
                if os.path.exists(path):
                    os.remove(path)

    def test_settings_auth_users_and_login_history(self):
        settings = db.get_app_settings()
        self.assertEqual(settings["app_name"], "Market POS")
        db.save_app_settings({"app_name": "Test POS", "theme": "green", "language": "en"})
        self.assertEqual(db.get_app_settings()["app_name"], "Test POS")

        admin = db.authenticate("admin", "admin123")
        self.assertIsNotNone(admin)
        db.log_login(admin)
        self.assertEqual(db.get_login_logs(1)[0]["username"], "admin")
        db.clear_login_logs()
        self.assertEqual(db.get_login_logs(), [])

        db.add_user("cashier", "pass", "cashier")
        user = [row for row in db.get_users() if row["username"] == "cashier"][0]
        db.save_app_settings({"theme": "light_blue", "language": "ru"}, user["id"])
        self.assertEqual(db.get_app_settings(user["id"])["language"], "ru")
        db.update_user(user["id"], "cashier2", "pass2", "admin")
        self.assertIsNotNone(db.authenticate("cashier2", "pass2"))
        db.delete_user(user["id"])
        self.assertFalse([row for row in db.get_users() if row["username"] == "cashier2"])

    def test_products_templates_categories_currencies_and_stock(self):
        cat_id = db.add_category("Texnika")
        db.update_category(cat_id, "Elektronika")
        self.assertEqual(db.get_categories()[0]["name"], "Elektronika")

        template_id = db.add_template("Telefon", [
            {"name": "Brend", "required": True},
            {"name": "Model", "field_type": "text"},
        ])
        fields = db.get_template_fields(template_id)
        self.assertEqual(len(fields), 2)
        db.update_template(template_id, "Smartfon", [{"name": "Brend"}])
        self.assertEqual(len(db.get_template_fields(template_id)), 1)

        supplier_id = db.add_supplier("Supplier")
        db.save_currency("GBP", "Pound", 16000)
        self.assertEqual(db.get_currency("GBP")["rate_to_uzs"], 16000)
        db.delete_currency("GBP")
        self.assertIsNone(db.get_currency("GBP"))

        product_id = db.add_product({
            "barcode": "P100",
            "name": "Phone",
            "template_id": template_id,
            "supplier_id": supplier_id,
            "category_id": cat_id,
            "price": 1200,
            "cost": 800,
            "stock": 10,
            "unit": "dona",
        })
        db.save_product_attributes(product_id, {fields[0]["id"]: "Apple"})
        self.assertEqual(db.get_product_attributes(product_id)[fields[0]["id"]], "Apple")
        product = db.get_product_by_barcode("P100")
        self.assertEqual(product["category_name"], "Elektronika")
        self.assertEqual(db.search_products("Pho")[0]["supplier_name"], "Supplier")

        db.add_stock(product_id, 5, "kirim")
        self.assertEqual(db.get_product_by_barcode("P100")["stock"], 15)
        db.update_product(product_id, {
            "barcode": "P101",
            "name": "Phone 2",
            "template_id": template_id,
            "supplier_id": supplier_id,
            "category_id": cat_id,
            "price": 1300,
            "cost": 850,
            "stock": 20,
            "unit": "dona",
        })
        self.assertEqual(db.get_product_by_barcode("P101")["name"], "Phone 2")
        db.put_product_in_process(product_id, 2, 100, "UZS", "Ali", "901")
        self.assertEqual(db.get_product_by_barcode("P101")["process_quantity"], 2)
        db.update_product_process(product_id, 4, 200, "USD", "Vali", "902")
        product = db.get_product_by_barcode("P101")
        self.assertEqual(product["stock"] - product["process_quantity"], 16)
        db.reduce_product_process(product_id, 1)
        self.assertEqual(db.get_product_by_barcode("P101")["process_quantity"], 3)
        db.clear_product_process(product_id)
        self.assertEqual(db.get_product_by_barcode("P101")["process_quantity"], 0)
        db.set_product_process_status(product_id, "process")
        self.assertEqual(db.get_product_by_barcode("P101")["process_status"], "process")
        db.delete_product(product_id)
        self.assertIsNone(db.get_product_by_barcode("P101"))

    def test_inventory_checking_flow(self):
        product_id = db.add_product({
            "barcode": "CHK1",
            "name": "Check Product",
            "template_id": None,
            "supplier_id": None,
            "category_id": None,
            "price": 100,
            "cost": 50,
            "stock": 3,
            "unit": "dona",
        })
        session_id = db.start_inventory_check()
        self.assertEqual(db.get_active_inventory_check()["id"], session_id)
        counts = db.get_inventory_check_counts(session_id)
        self.assertEqual(counts["total"], 1)
        item = db.mark_inventory_product_checked(session_id, "CHK1", 1)
        self.assertIsNone(item["checked_at"])
        item = db.mark_inventory_product_checked(session_id, "CHK1", 2)
        self.assertIsNotNone(item["checked_at"])
        self.assertEqual(len(db.get_inventory_check_items(session_id, True)), 1)
        result = db.finish_inventory_check(session_id)
        self.assertEqual(result["checked_quantity"], 3)
        self.assertIsNone(db.get_active_inventory_check())
        self.assertEqual(db.get_product_by_barcode("CHK1")["id"], product_id)

    def test_sales_returns_reports_and_clear_history(self):
        customer_id = db.add_customer("Customer", "99890", "c@example.com")
        db.update_customer(customer_id, "Customer 2", "99891", "c2@example.com")
        self.assertEqual(db.get_all_customers()[0]["name"], "Customer 2")
        admin = db.authenticate("admin", "admin123")
        product_id = db.add_product({
            "barcode": "SALE1",
            "name": "Sale Product",
            "template_id": None,
            "supplier_id": None,
            "category_id": None,
            "price": 1000,
            "cost": 600,
            "stock": 10,
            "unit": "dona",
        })
        sale_id = db.create_sale(
            customer_id,
            admin["id"],
            [{"product_id": product_id, "quantity": 3, "price": 1000, "subtotal": 3000}],
            3000,
            100,
            2900,
            "naqd",
            customer_name="Manual Customer",
            customer_phone="999",
        )
        self.assertEqual(db.get_sales_today()[0]["id"], sale_id)
        self.assertEqual(db.get_sale_items(sale_id)[0]["product_name"], "Sale Product")
        archive = db.get_product_sales_archive("Manual")
        self.assertEqual(archive[0]["customer_phone"], "999")
        self.assertEqual(db.get_sale_cost(sale_id), 1800)

        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(db.get_daily_report(today)["count"], 1)
        self.assertTrue(db.get_sales_by_date(today))
        self.assertTrue(db.get_cashier_report(today))
        self.assertTrue(db.get_cashier_sold_items(today))
        self.assertTrue(db.get_overall_period_series("2000-01-01", "2999-01-01"))
        self.assertTrue(db.get_cashier_period_summary("2000-01-01", "2999-01-01"))
        self.assertTrue(db.get_customer_period_summary("2000-01-01", "2999-01-01"))
        self.assertTrue(db.get_entity_period_series("cashier", admin["id"], "2000-01-01", "2999-01-01"))
        self.assertTrue(db.get_entity_period_series("customer", customer_id, "2000-01-01", "2999-01-01"))

        db.return_sale_item(archive[0]["sale_item_id"], 1, "return")
        self.assertEqual(db.get_product_by_barcode("SALE1")["stock"], 8)
        db.clear_sales_history()
        self.assertEqual(db.get_product_sales_archive(), [])

    def test_suppliers_debtors_and_expenses(self):
        supplier_id = db.add_supplier("Supplier", "1", "note", "USD")
        db.update_supplier(supplier_id, "Supplier 2", "2", "note2", "EUR")
        db.add_supplier_debt(supplier_id, 100, "debt")
        db.pay_supplier_debt(supplier_id, 40, "pay")
        self.assertEqual(db.get_all_suppliers()[0]["balance"], 60)
        self.assertEqual(len(db.get_supplier_debt_movements(supplier_id)), 2)

        debtor_id = db.add_debtor("Debtor", "1", "note", "USD")
        db.update_debtor(debtor_id, "Debtor 2", "2", "note2", "EUR")
        db.add_debtor_debt(debtor_id, 80, "debt")
        db.pay_debtor_debt(debtor_id, 30, "pay")
        self.assertEqual(db.get_all_debtors()[0]["balance"], 50)
        self.assertEqual(len(db.get_debtor_debt_movements(debtor_id)), 2)

        category_id = db.add_expense_category("Office")
        db.update_expense_category(category_id, "Office 2")
        expense_id = db.add_expense(category_id, 25, "UZS", "paper")
        db.update_expense(expense_id, category_id, 30, "USD", "paper2")
        self.assertEqual(db.get_expenses()[0]["category_name"], "Office 2")
        self.assertEqual(db.get_expense_report("2000-01-01", "2999-01-01")[0]["amount"], 30)
        self.assertEqual(db.get_expense_category_report("2000-01-01", "2999-01-01")[0]["category_name"], "Office 2")
        db.delete_expense(expense_id)
        db.delete_expense_category(category_id)
        self.assertEqual(db.get_expenses(), [])

        db.delete_supplier(supplier_id)
        db.delete_debtor(debtor_id)
        self.assertEqual(db.get_all_suppliers(), [])
        self.assertEqual(db.get_all_debtors(), [])


if __name__ == "__main__":
    unittest.main()
