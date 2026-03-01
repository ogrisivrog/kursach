"""
Единая программа парсинга товаров с Wildberries и Яндекс.Маркета.
Для каждого поискового запроса собирает результаты с обеих площадок
и сохраняет топ-3 товара с самыми низкими ценами.
"""

import time
import csv
from pathlib import Path

# Путь к CSV (относительно корня проекта Kursach)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CSV_FILE_PATH = PROJECT_ROOT / "data" / "sellers" / "data_sellers.csv"


def parse_price_to_float(price_str):
    """
    Преобразует строку цены в число для сортировки.
    """
    if not price_str or price_str == "Цена не указана":
        return float("inf")  # товары без цены в конец
    cleaned = "".join(c for c in str(price_str) if c.isdigit() or c in ".,")
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return float("inf")


def get_top_3_by_price(products_wb, products_ym, search_query):
    """
    Объединяет результаты WB и YM, сортирует по цене и возвращает топ-3.
    
    Args:
        products_wb: список товаров с Wildberries
        products_ym: список товаров с Яндекс.Маркета
        search_query: поисковый запрос
        
    Returns:
        list: топ-3 товара с самыми низкими ценами
    """
    combined = []
    
    for p in products_wb or []:
        item = dict(p)
        item["marketplace"] = "Wildberries"
        combined.append(item)
    
    for p in products_ym or []:
        item = dict(p)
        item["marketplace"] = "Яндекс.Маркет"
        combined.append(item)
    
    # Сортируем по цене (числовое значение)
    combined.sort(key=lambda x: parse_price_to_float(x.get("price", "")))
    
    # Берём топ-3
    top3 = combined[:3]
    
    # Обновляем number для вывода (1, 2, 3)
    for i, item in enumerate(top3, 1):
        item["number"] = i
    
    return top3


def save_top3_to_csv(products, search_query):
    """
    Сохраняет топ-3 товара в CSV.
    """
    if not products:
        print("Нет данных для сохранения в CSV")
        return

    CSV_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = CSV_FILE_PATH.is_file()
    fieldnames = ["search_query", "number", "brand", "name", "price", "link", "marketplace"]

    with open(str(CSV_FILE_PATH), "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        if not file_exists:
            writer.writeheader()
        for product in products:
            row = {
                "search_query": search_query,
                "number": product.get("number", ""),
                "brand": product.get("brand", ""),
                "name": product.get("name", ""),
                "price": product.get("price", ""),
                "link": product.get("link", ""),
                "marketplace": product.get("marketplace", ""),
            }
            writer.writerow(row)

    print(f"Топ-3 для '{search_query}' добавлены в CSV: {CSV_FILE_PATH}")


def get_products_list():
    """Получает список товаров для поиска."""
    print("\nВведите названия товаров для поиска (по одному на строку).")
    print("Для завершения ввода введите пустую строку или 'stop':")

    products = ["iphone 17 pro max", "iphone 16 pro max", "iphone 15 pro max", "iphone 14 pro max"]
    counter = 0
    if len(products) != 0:
        counter = 1
    while True:
        if counter == 1:
            break
        product = input(f"Товар {len(products) + 1}: ").strip()
        if not product or product.lower() == "stop":
            break
        products.append(product)

    return products


def main():
    # Импорты внутри main, чтобы при сбое одного парсера другой можно было подключать отдельно
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from parser_price_WB import (
        get_browser,
        search_and_parse_product as search_wb,
    )
    from praser_price_YM import (
        BASE_URL as YM_BASE_URL,
        search_and_parse_product as search_ym,
    )

    print("\n" + "=" * 60)
    print("ЕДИНЫЙ ПАРСЕР: Wildberries + Яндекс.Маркет")
    print("Сохранение топ-3 товаров с самыми низкими ценами")
    print("=" * 60)

    products_list = get_products_list()

    if not products_list:
        print("Список товаров пуст. Программа завершена.")
        return

    print(f"\nБудет обработано товаров: {len(products_list)}")
    for i, product in enumerate(products_list, 1):
        print(f"  {i}. {product}")

    # max_cards_input = input(
    #     "\nСколько карточек спарсить с каждой площадки (по умолчанию 10): "
    # ) 
    max_cards_input = 3 # сколько карточек по каждому товару парсить
    max_cards = int(max_cards_input or "10")

    print(f"\nНачинаем обработку {len(products_list)} товаров...")
    print("Фаза 1: все товары на WB → Фаза 2: все товары на YM → объединение и топ-3\n")

    driver = get_browser()
    from selenium.webdriver.support.ui import WebDriverWait

    wait = WebDriverWait(driver, 20)

    try:
        all_results = []
        results_wb = {}  # product_name -> list
        results_ym = {}  # product_name -> list

        # Фаза 1: парсим все товары на Wildberries (драйвер остаётся на WB)
        print("=" * 60)
        print("ФАЗА 1: WILDBERRIES")
        print("=" * 60)
        for idx, product_name in enumerate(products_list, 1):
            print(f"\n[{idx}/{len(products_list)}] WB: {product_name}")
            products_wb = search_wb(driver, wait, product_name, max_cards)
            results_wb[product_name] = products_wb
            if idx < len(products_list):
                time.sleep(3)

        # Фаза 2: парсим все товары на Яндекс.Маркете (открываем YM один раз, как в оригинале)
        print("\n" + "=" * 60)
        print("ФАЗА 2: ЯНДЕКС.МАРКЕТ")
        print("=" * 60)
        driver.get(YM_BASE_URL)
        time.sleep(5)
        for idx, product_name in enumerate(products_list, 1):
            print(f"\n[{idx}/{len(products_list)}] YM: {product_name}")
            products_ym = search_ym(driver, wait, product_name, max_cards)
            results_ym[product_name] = products_ym
            if idx < len(products_list):
                time.sleep(3)

        # Объединяем, выбираем топ-3 и сохраняем для каждого товара
        print("\n" + "=" * 60)
        print("ОБЪЕДИНЕНИЕ РЕЗУЛЬТАТОВ")
        print("=" * 60)
        for product_name in products_list:
            products_wb = results_wb.get(product_name, [])
            products_ym = results_ym.get(product_name, [])
            top3 = get_top_3_by_price(products_wb, products_ym, product_name)

            if top3:
                save_top3_to_csv(top3, product_name)
                all_results.extend(top3)
                print(f"\nТоп-3 для '{product_name}':")
                for p in top3:
                    name_preview = (p.get("name") or "")[:40]
                    print(f"  {p['number']}. [{p['marketplace']}] {p.get('brand', '')} {name_preview}... - {p.get('price', '')}")
            else:
                print(f"Для '{product_name}' не найдено результатов.")

        print("\n" + "=" * 60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        print(f"Обработано товаров: {len(products_list)}")
        print(f"Всего записано в CSV: {len(all_results)}")
        print(f"Файл: {CSV_FILE_PATH}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
