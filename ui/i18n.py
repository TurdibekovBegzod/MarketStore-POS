from PyQt6.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QTableWidget, QTabWidget,
    QComboBox, QGroupBox
)


TRANSLATIONS = {
    "en": {
        "Sotuv": "Sales",
        "Mahsulotlar": "Products",
        "Ombor": "Stock",
        "Hisobotlar": "Reports",
        "Qarzlar": "Debts",
        "Harajatlar": "Expenses",
        "Tekshiruv": "Checking",
        "Checking": "Checking",
        "Kassirlar": "Cashiers",
        "Kirish tarixi": "Login history",
        "Sozlamalar": "Settings",
        "Interfeys rangi": "Interface theme",
        "Til": "Language",
        "Dastur nomi": "App name",
        "Saqlash": "Save",
        "Bekor": "Cancel",
        "Bekor qilish": "Cancel",
        "Yopish": "Close",
        "Chiqish": "Logout",
        "Yangilash": "Refresh",
        "Tarixni tozalash": "Clear history",
        "Sana:": "Date:",
        "Bugun": "Today",
        "Haftalik": "Weekly",
        "Oylik": "Monthly",
        "Daromad": "Revenue",
        "Foyda": "Profit",
        "Sotuvlar soni": "Sales count",
        "Mahsulotlar soni": "Products count",
        "O'rtacha chek": "Average check",
        "Hisobot turi:": "Report type:",
        "Umumiy": "Overall",
        "Kassirlar hisoboti": "Cashier report",
        "Grafik:": "Chart:",
        "Cheklar": "Checks",
        "Tanlangan hisobot grafigi": "Selected report chart",
        "Nomi": "Name",
        "Mahsulot": "Product",
        "Qoldiq": "Stock",
        "Amal": "Action",
        "Amallar": "Actions",
        "Narx": "Price",
        "Xarid": "Cost",
        "Miqdor": "Quantity",
        "Jami": "Total",
        "Vaqt": "Time",
        "Sotuv": "Sale",
        "Sotildi": "Sold",
        "Qaytdi": "Returned",
        "To'lov": "Payment",
        "Valyuta": "Currency",
        "Summa": "Amount",
        "Kategoriya": "Category",
        "Description": "Description",
        "Username": "Username",
        "Role": "Role",
        "Yaratilgan": "Created",
        "Telefon": "Phone",
        "Qarz": "Debt",
        "Jami olingan": "Total received",
        "Jami berilgan": "Total given",
        "O'rtacha": "Average",
        "Kassir": "Cashier",
        "Admin": "Admin",
        "Template": "Template",
        "Shtrix-kod": "Barcode",
        "Sanaldi": "Counted",
        "Farq": "Difference",
        "Qoldi": "Remaining",
        "Zaklad": "Deposit",
        "Bor mahsulotlar": "Available",
        "Jarayonda": "In process",
        "Sotilganlar": "Sold",
        "Barcha ta'minotchilar": "All suppliers",
        "Ta'minotchi tanlanmagan": "No supplier",
        "Barcha templatelar": "All templates",
        "Template tanlanmagan": "No template",
        "Templatelar": "Templates",
        "+ Mahsulot qo'shish": "+ Add product",
        "Jarayonga": "Process",
        "Tahrir": "Edit",
        "O'chir": "Delete",
        "Qaytarish": "Return",
        "Bor mahsulotlarga": "Available",
        "Sotuvni yakunlash": "Complete sale",
        "Kategoriyalar": "Categories",
        "+ Harajat": "+ Expense",
        "+ Kirim qo'shish": "+ Add stock",
        "+ Kirim": "+ Stock",
        "+ Kassir qo'shish": "+ Add cashier",
        "Tarix": "History",
        "+ Ta'minotchi": "+ Supplier",
        "+ Qarz oluvchi": "+ Debtor",
        "Olgan qarzlar": "Received debts",
        "Bergan qarzlar": "Given debts",
        "Kirim qo'shish": "Add stock",
        "Mahsulot:": "Product:",
        "Miqdor:": "Quantity:",
        "Izoh:": "Note:",
        "Ixtiyoriy izoh": "Optional note",
        "Savat": "Cart",
        "Chegirma:": "Discount:",
        "To'lash:": "Pay:",
        "To'lov:": "Payment:",
        "Valyuta:": "Currency:",
        "Kurslar": "Rates",
        "Sotishni yakunlash": "Complete sale",
        "Savatni tozalash": "Clear cart",
        "Mahsulot qidirish...": "Search product...",
        "Qidirish...": "Search...",
        "Mahsulot nomi yoki shtrix-kod... Skaner Enter yuborsa savatga qo'shiladi": "Product name or barcode... Scanner Enter adds to cart",
        "Checking boshlanmagan": "Checking has not started",
        "Tekshirishni boshlash": "Start checking",
        "Jarayonni tugatish": "Finish process",
        "Shtrix-kod:": "Barcode:",
        "Skaner bilan o'qing yoki barcode kiriting...": "Scan or enter barcode...",
        "Tekshirish": "Check",
        "Tekshiruvdan o'tganlar": "Checked products",
        "Tekshiruvdan o'tmaganlar": "Unchecked products",
        "Sanaldi": "Counted",
        "Qoldi": "Remaining",
        "Farq": "Difference",
    },
    "ru": {
        "Tekshiruv": "Проверка",
        "Checking": "Проверка",
        "Checking boshlanmagan": "Проверка не начата",
        "Tekshirishni boshlash": "Начать проверку",
        "Jarayonni tugatish": "Завершить процесс",
        "Shtrix-kod:": "Штрихкод:",
        "Skaner bilan o'qing yoki barcode kiriting...": "Сканируйте или введите штрихкод...",
        "Tekshirish": "Проверить",
        "Tekshiruvdan o'tganlar": "Проверенные товары",
        "Tekshiruvdan o'tmaganlar": "Непроверенные товары",
        "Miqdor:": "Количество:",
        "Sanaldi": "Посчитано",
        "Qoldi": "Осталось",
        "Farq": "Разница",
        "Sotuv": "Продажи",
        "Mahsulotlar": "Товары",
        "Ombor": "Склад",
        "Hisobotlar": "Отчеты",
        "Qarzlar": "Долги",
        "Harajatlar": "Расходы",
        "Kassirlar": "Кассиры",
        "Kirish tarixi": "История входов",
        "Sozlamalar": "Настройки",
        "Interfeys rangi": "Тема интерфейса",
        "Til": "Язык",
        "Dastur nomi": "Название программы",
        "Saqlash": "Сохранить",
        "Bekor": "Отмена",
        "Bekor qilish": "Отмена",
        "Yopish": "Закрыть",
        "Chiqish": "Выход",
        "Yangilash": "Обновить",
        "Tarixni tozalash": "Очистить историю",
        "Sana:": "Дата:",
        "Bugun": "Сегодня",
        "Haftalik": "Неделя",
        "Oylik": "Месяц",
        "Daromad": "Выручка",
        "Foyda": "Прибыль",
        "Sotuvlar soni": "Кол-во продаж",
        "Mahsulotlar soni": "Кол-во товаров",
        "O'rtacha chek": "Средний чек",
        "Hisobot turi:": "Тип отчета:",
        "Umumiy": "Общий",
        "Kassirlar hisoboti": "Отчет кассиров",
        "Grafik:": "График:",
        "Cheklar": "Чеки",
        "Tanlangan hisobot grafigi": "График выбранного отчета",
        "Nomi": "Название",
        "Mahsulot": "Товар",
        "Qoldiq": "Остаток",
        "Amal": "Действие",
        "Amallar": "Действия",
        "Narx": "Цена",
        "Xarid": "Себестоимость",
        "Miqdor": "Количество",
        "Jami": "Итого",
        "Vaqt": "Время",
        "Sotuv": "Продажа",
        "Sotildi": "Продано",
        "Qaytdi": "Возврат",
        "To'lov": "Оплата",
        "Valyuta": "Валюта",
        "Summa": "Сумма",
        "Kategoriya": "Категория",
        "Description": "Описание",
        "Username": "Логин",
        "Role": "Роль",
        "Yaratilgan": "Создано",
        "Telefon": "Телефон",
        "Qarz": "Долг",
        "Jami olingan": "Всего получено",
        "Jami berilgan": "Всего выдано",
        "O'rtacha": "Среднее",
        "Kassir": "Кассир",
        "Admin": "Админ",
        "Template": "Шаблон",
        "Shtrix-kod": "Штрихкод",
        "Zaklad": "Залог",
        "Bor mahsulotlar": "В наличии",
        "Jarayonda": "В процессе",
        "Sotilganlar": "Проданные",
        "Barcha ta'minotchilar": "Все поставщики",
        "Ta'minotchi tanlanmagan": "Без поставщика",
        "Barcha templatelar": "Все шаблоны",
        "Template tanlanmagan": "Без шаблона",
        "Templatelar": "Шаблоны",
        "+ Mahsulot qo'shish": "+ Добавить товар",
        "Jarayonga": "В процесс",
        "Tahrir": "Изменить",
        "O'chir": "Удалить",
        "Qaytarish": "Вернуть",
        "Bor mahsulotlarga": "В наличие",
        "Sotuvni yakunlash": "Завершить продажу",
        "Kategoriyalar": "Категории",
        "+ Harajat": "+ Расход",
        "+ Kirim qo'shish": "+ Добавить приход",
        "+ Kirim": "+ Приход",
        "+ Kassir qo'shish": "+ Добавить кассира",
        "Tarix": "История",
        "+ Ta'minotchi": "+ Поставщик",
        "+ Qarz oluvchi": "+ Должник",
        "Olgan qarzlar": "Полученные долги",
        "Bergan qarzlar": "Выданные долги",
        "Kirim qo'shish": "Добавить приход",
        "Mahsulot:": "Товар:",
        "Miqdor:": "Количество:",
        "Izoh:": "Примечание:",
        "Ixtiyoriy izoh": "Необязательное примечание",
        "Savat": "Корзина",
        "Chegirma:": "Скидка:",
        "To'lash:": "К оплате:",
        "To'lov:": "Оплата:",
        "Valyuta:": "Валюта:",
        "Kurslar": "Курсы",
        "Sotishni yakunlash": "Завершить продажу",
        "Savatni tozalash": "Очистить корзину",
        "Mahsulot qidirish...": "Поиск товара...",
        "Qidirish...": "Поиск...",
        "Mahsulot nomi yoki shtrix-kod... Skaner Enter yuborsa savatga qo'shiladi": "Название товара или штрихкод... Enter со сканера добавит в корзину",
    },
}


def t(text, language="uz"):
    if language == "uz" or not text:
        return text
    raw = str(text)
    stripped = raw.strip()
    prefix = raw[:len(raw) - len(raw.lstrip())]
    suffix = raw[len(raw.rstrip()):]
    translated = TRANSLATIONS.get(language, {}).get(stripped)
    return f"{prefix}{translated}{suffix}" if translated else raw


def is_translatable(text):
    stripped = str(text or "").strip()
    return any(stripped in language_map for language_map in TRANSLATIONS.values())


def set_language(widget, language="uz"):
    widget.setProperty("app_language", language)
    for child in widget.findChildren((QLabel, QPushButton, QLineEdit, QGroupBox)):
        if child.property("i18n_skip"):
            continue
        if isinstance(child, (QLabel, QPushButton, QGroupBox)):
            original = child.property("i18n_original_text")
            if original is None:
                if not is_translatable(child.text()):
                    continue
                original = child.text()
                child.setProperty("i18n_original_text", original)
            if not is_translatable(original):
                continue
            child.setText(t(original, language))
        if isinstance(child, QLineEdit):
            original = child.property("i18n_original_placeholder")
            if original is None:
                if not is_translatable(child.placeholderText()):
                    continue
                original = child.placeholderText()
                child.setProperty("i18n_original_placeholder", original)
            if not is_translatable(original):
                continue
            child.setPlaceholderText(t(original, language))

    for table in widget.findChildren(QTableWidget):
        for column in range(table.columnCount()):
            item = table.horizontalHeaderItem(column)
            if not item:
                continue
            original = item.data(257)
            if original is None:
                if not is_translatable(item.text()):
                    continue
                original = item.text()
                item.setData(257, original)
            if not is_translatable(original):
                continue
            item.setText(t(original, language))

    for tabs in widget.findChildren(QTabWidget):
        for index in range(tabs.count()):
            key = f"i18n_tab_{index}"
            original = tabs.property(key)
            if original is None:
                if not is_translatable(tabs.tabText(index)):
                    continue
                original = tabs.tabText(index)
                tabs.setProperty(key, original)
            if not is_translatable(original):
                continue
            tabs.setTabText(index, t(original, language))

    for combo in widget.findChildren(QComboBox):
        for index in range(combo.count()):
            data = combo.itemData(index)
            if data not in (None, "none", "week", "month"):
                continue
            key = f"i18n_item_{index}_{data}"
            original = combo.property(key)
            if original is None:
                if not is_translatable(combo.itemText(index)):
                    continue
                original = combo.itemText(index)
                combo.setProperty(key, original)
            if not is_translatable(original):
                continue
            combo.setItemText(index, t(original, language))
