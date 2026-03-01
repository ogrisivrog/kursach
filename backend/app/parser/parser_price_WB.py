import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from datetime import datetime
import csv
import os

BASE_URL = "https://www.wildberries.ru"
CSV_FILE_PATH = "/Users/denis/Desktop/Рабочий стол/ВУЗ/Романчева/Kursach/data/sellers/data_sellers.csv"


def get_browser():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--headless")  # убрать если нужно окно

    # Указываем версию Chrome, чтобы uc скачал подходящий драйвер
    driver = uc.Chrome(version_main=144, options=options)
    return driver


def apply_sorting(driver, wait, sort_type="price_asc"):
    """
    Применяет сортировку на Wildberries несколькими способами
    """
    sort_options = {
        "price_asc": ["возрастанию", "по возрастанию", "дешевые"],
        "price_desc": ["убыванию", "по убыванию", "дорогие"],
        "popular": ["популярности", "популярные"],
        "rating": ["рейтингу", "по рейтингу"]
    }

    keywords = sort_options.get(sort_type, ["возрастанию"])

    try:
        print("Пытаемся найти и открыть выпадающий список сортировки...")

        # СПОСОБ 1: Пробуем найти кнопку сортировки по разным селекторам
        sort_selectors = [
            "//button[contains(@class, 'sorting')]",
            "//div[contains(@class, 'dropdown-filter')]//button",
            "//*[contains(@class, 'sort')]//button",
            "//span[contains(text(), 'Сортировка')]/..",
            "//div[contains(@class, 'dropdown-filter__btn')]",
            "//button[contains(@aria-label, 'Сортировка')]",
            "//*[@id='catalog-sorting']",
            "//div[contains(@class, 'catalog-sorting')]//button"
        ]

        sort_button = None
        for selector in sort_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    sort_button = elements[0]
                    print(f"Нашли кнопку сортировки по селектору: {selector}")
                    break
            except:
                continue

        if not sort_button:
            # Если не нашли по XPath, ищем по CSS
            css_selectors = [
                ".sorting-panel .dropdown-filter__btn",
                ".catalog-sorting .dropdown-filter__btn",
                "[class*='sorting'] button",
                ".dropdown-filter__btn"
            ]

            for selector in css_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        sort_button = elements[0]
                        print(f"Нашли кнопку сортировки по CSS: {selector}")
                        break
                except:
                    continue

        if not sort_button:
            print("Не удалось найти кнопку сортировки")
            return False

        # Прокручиваем к кнопке
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", sort_button)
        time.sleep(1)

        # СПОСОБ 1: Наведение мыши
        print("Наводим мышь на кнопку сортировки...")
        actions = ActionChains(driver)
        actions.move_to_element(sort_button).perform()
        time.sleep(2)

        # СПОСОБ 2: Пробуем кликнуть (иногда работает лучше наведения)
        try:
            print("Пробуем кликнуть на кнопку...")
            driver.execute_script("arguments[0].click();", sort_button)
            time.sleep(1)
        except:
            pass

        # Ищем элементы выпадающего списка
        print("Ищем элементы сортировки...")

        # Селекторы для элементов списка
        item_selectors = [
            "//li[contains(@class, 'dropdown-filter__item')]",
            "//div[contains(@class, 'dropdown-filter__item')]",
            "//a[contains(@class, 'sorting__link')]",
            "//li//span[contains(text(), 'цен')]/..",
            "//li//span[contains(text(), 'популяр')]/..",
            "//div[@role='listbox']//div[@role='option']",
            "//ul[contains(@class, 'dropdown-filter__list')]/li",
            "//*[contains(@class, 'sorting__item')]"
        ]

        sort_items = []
        for selector in item_selectors:
            try:
                items = driver.find_elements(By.XPATH, selector)
                if items:
                    sort_items = items
                    print(
                        f"Нашли элементы списка по селектору: {selector}, всего: {len(items)}")
                    break
            except:
                continue

        if not sort_items:
            # Пробуем найти по CSS
            css_item_selectors = [
                ".dropdown-filter__list .dropdown-filter__item",
                ".sorting__list .sorting__item",
                "[role='option']",
                ".catalog-sorting__list .catalog-sorting__item"
            ]

            for selector in css_item_selectors:
                try:
                    items = driver.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        sort_items = items
                        print(
                            f"Нашли элементы списка по CSS: {selector}, всего: {len(items)}")
                        break
                except:
                    continue

        if sort_items:
            print("Найденные варианты сортировки:")
            for item in sort_items:
                try:
                    text = item.text.strip()
                    if text:
                        print(f"  - {text}")
                except:
                    pass

            # Ищем нужный вариант по ключевым словам
            for item in sort_items:
                try:
                    item_text = item.text.lower()
                    for keyword in keywords:
                        if keyword.lower() in item_text:
                            print(f"Нашли нужный вариант: {item.text}")
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});", item)
                            time.sleep(0.5)
                            driver.execute_script(
                                "arguments[0].click();", item)
                            print("Применили сортировку")
                            time.sleep(2)
                            return True
                except Exception as e:
                    continue

        # Если не нашли через поиск элементов, пробуем прямой XPath
        print("Пробуем прямой XPath для сортировки по цене...")
        price_asc_xpaths = [
            "//li[contains(text(), 'По возрастанию цены')]",
            "//span[contains(text(), 'возрастанию')]/..",
            "//*[contains(text(), 'возрастанию')][contains(@class, 'item')]",
            "//button[@data-sort='price']",
            "//a[@data-sort='price']"
        ]

        for xpath in price_asc_xpaths:
            try:
                element = wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath)))
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", element)
                print(f"Клик по XPath: {xpath}")
                time.sleep(2)
                return True
            except:
                continue

        print("Не удалось применить сортировку")
        return False

    except Exception as e:
        print(f"Ошибка при сортировке: {e}")
        return False


def parse_product_cards(driver, max_cards=10):
    """
    Парсит информацию с карточек товаров

    Args:
        driver: экземпляр веб-драйвера
        max_cards (int): максимальное количество карточек для парсинга

    Returns:
        list: список словарей с информацией о товарах
    """
    products = []

    try:
        # Ждем загрузки карточек товаров
        time.sleep(3)

        # Находим все карточки товаров
        card_xpath = "/html/body/div[2]/main/div[2]/div[1]/div/div[1]/div/div/div[4]/div[1]/div/div/article"
        product_cards = driver.find_elements(By.XPATH, card_xpath)

        print(f"Найдено карточек товаров: {len(product_cards)}")

        # Ограничиваем количество карточек для парсинга
        cards_to_parse = product_cards[:max_cards]

        for i, card in enumerate(cards_to_parse, 1):
            try:
                product_info = {}

                # Получаем ссылку на товар
                try:
                    link_element = card.find_element(By.XPATH, ".//a")
                    product_info['link'] = link_element.get_attribute('href')
                except:
                    product_info['link'] = None

                # Получаем название производителя (может отсутствовать)
                try:
                    brand_xpath = ".//div[contains(@class, 'product-card__brand')]//span[1]"
                    brand_elements = card.find_elements(By.XPATH, brand_xpath)
                    if brand_elements:
                        product_info['brand'] = brand_elements[0].text.strip()
                    else:
                        # Альтернативный XPath для производителя
                        alt_brand_xpath = ".//h2/span[1]"
                        alt_brand = card.find_elements(
                            By.XPATH, alt_brand_xpath)
                        if alt_brand:
                            brand_text = alt_brand[0].text.strip()
                            product_info['brand'] = brand_text if brand_text else "Не указан"
                        else:
                            product_info['brand'] = "Не указан"
                except Exception as e:
                    product_info['brand'] = "Не указан"
                    print(
                        f"  Ошибка при получении бренда для карточки {i}: {e}")

                # Получаем название товара
                try:
                    # Пробуем разные селекторы для названия
                    name_selectors = [
                        ".//h2/span[2]",
                        ".//h2/span[last()]",
                        ".//div[contains(@class, 'product-card__name')]",
                        ".//h2"
                    ]

                    name_text = None
                    for selector in name_selectors:
                        name_elements = card.find_elements(By.XPATH, selector)
                        if name_elements:
                            raw_name = name_elements[0].text.strip()
                            if raw_name and len(raw_name) > 3:
                                # Очищаем название от лишних символов
                                import re
                                # Оставляем только буквы, цифры и пробелы
                                cleaned_name = re.sub(r'[^\w\s-]', ' ', raw_name)
                                # Заменяем множественные пробелы на один
                                cleaned_name = ' '.join(cleaned_name.split())
                                # Убираем пробелы в начале и конце
                                cleaned_name = cleaned_name.strip()
                                
                                name_text = cleaned_name
                                break

                    product_info['name'] = name_text if name_text else "Не указано"
                except Exception as e:
                    product_info['name'] = "Не указано"
                    print(
                        f"  Ошибка при получении названия для карточки {i}: {e}")

                # Получаем цену
                try:
                    # Пробуем разные селекторы для цены
                    price_selectors = [
                        ".//span/span/ins",
                        ".//span[contains(@class, 'price')]//ins",
                        ".//ins[contains(@class, 'price')]",
                        ".//span[@class='price']",
                        ".//*[contains(@class, 'price__lower')]"
                    ]

                    price_text = None
                    for selector in price_selectors:
                        price_elements = card.find_elements(By.XPATH, selector)
                        if price_elements:
                            price_text = price_elements[0].text.strip()
                            if price_text:
                                # Очищаем цену от символов валюты и пробелов
                                price_text = ''.join(
                                    c for c in price_text if c.isdigit() or c in '.,')
                                break

                    product_info['price'] = price_text if price_text else "Цена не указана"
                except Exception as e:
                    product_info['price'] = "Цена не указана"
                    print(f"  Ошибка при получении цены для карточки {i}: {e}")

                # Добавляем номер карточки
                product_info['number'] = i

                products.append(product_info)
                print(
                    f"  Карточка {i}: {product_info.get('brand', '')} {product_info.get('name', '')[:50]}... - {product_info.get('price', '')}")

            except Exception as e:
                print(f"Ошибка при парсинге карточки {i}: {e}")
                continue

        return products

    except Exception as e:
        print(f"Ошибка при парсинге карточек: {e}")
        return products


def save_to_csv(products, search_query):
    """
    Сохраняет результаты в CSV файл по указанному пути

    Args:
        products (list): список словарей с информацией о товарах
        search_query (str): поисковый запрос
    """
    if not products:
        print("Нет данных для сохранения в CSV")
        return

    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)

    # Проверяем, существует ли файл и нужно ли писать заголовки
    file_exists = os.path.isfile(CSV_FILE_PATH)

    # Определяем заголовки (добавляем поле search_query для идентификации товара)
    fieldnames = ['search_query', 'number', 'brand', 'name', 'price', 'link']

    # Сохраняем в CSV (режим 'a' для добавления, чтобы сохранить все товары)
    with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')

        # Пишем заголовки только если файл новый
        if not file_exists:
            writer.writeheader()

        for product in products:
            row = {
                'search_query': search_query,
                'number': product.get('number', ''),
                'brand': product.get('brand', ''),
                'name': product.get('name', ''),
                'price': product.get('price', ''),
                'link': product.get('link', '')
            }
            writer.writerow(row)

    print(
        f"Результаты для '{search_query}' добавлены в CSV файл: {CSV_FILE_PATH}")


def search_and_parse_product(driver, wait, product_name, max_cards):
    """
    Выполняет поиск и парсинг для одного товара на Wildberries

    Args:
        driver: экземпляр веб-драйвера
        wait: WebDriverWait
        product_name (str): название товара для поиска
        max_cards (int): количество карточек для парсинга

    Returns:
        list: список спарсенных товаров
    """
    print(f"\n{'='*60}")
    print(f"ОБРАБОТКА ТОВАРА: {product_name}")
    print(f"{'='*60}")

    # Всегда возвращаемся на главную страницу для надежности
    print("Переходим на главную страницу...")
    driver.get(BASE_URL)
    time.sleep(3)

    # --- поиск ---
    print("Выполняем поиск...")
    try:
        # Ищем поле поиска
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "searchInput"))
        )

        # Очищаем поле (хотя оно уже должно быть пустым, но для надежности)
        search_input.click()
        search_input.clear()

        # Вводим новый запрос
        search_input.send_keys(product_name)
        time.sleep(1)
        search_input.send_keys(Keys.ENTER)

    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        return []

    # ждём загрузки результатов
    print("Ждем загрузки результатов...")
    time.sleep(5)

    # Применяем сортировку
    print("Пытаемся применить сортировку...")
    apply_sorting(driver, wait, "price_asc")

    print("Поиск выполнен и применена сортировка по цене.")

    # Парсим карточки товаров
    print(f"\nНачинаем парсинг первых {max_cards} карточек...")
    products = parse_product_cards(driver, max_cards)

    return products


def get_products_list():
    """
    Получает список товаров от пользователя

    Returns:
        list: список названий товаров
    """
    print("\nВведите названия товаров для поиска на Wildberries (по одному на строку).")
    print("Для завершения ввода введите пустую строку или 'stop':")

    products = [] # Список товаров
    counter = 0
    if len(products) != 0:
        counter = 1
    while True:
        if counter == 1:
            break
        product = input(f"Товар {len(products) + 1}: ").strip()
        if not product or product.lower() == 'stop':
            break
        if product:
            products.append(product)

    return products


def main():
    print("\n" + "="*60)
    print("ПАРСЕР WILDBERRIES - ПАКЕТНАЯ ОБРАБОТКА")
    print("="*60)

    # Получаем список товаров
    products_list = get_products_list()

    if not products_list:
        print("Список товаров пуст. Программа завершена.")
        return

    print(f"\nБудет обработано товаров: {len(products_list)}")
    for i, product in enumerate(products_list, 1):
        print(f"  {i}. {product}")

    max_cards = int(input(
        "\nСколько карточек спарсить для каждого товара (по умолчанию 10): ") or "10")

    print(f"\nНачинаем обработку {len(products_list)} товаров...")

    driver = get_browser()
    wait = WebDriverWait(driver, 20)

    try:
        all_results = []

        # Обрабатываем каждый товар
        for idx, product_name in enumerate(products_list, 1):
            print(f"\n[{idx}/{len(products_list)}] Обработка товара...")

            products = search_and_parse_product(
                driver, wait, product_name, max_cards)

            if products:
                save_to_csv(products, product_name)
                all_results.extend(products)

                print(f"\nРезультаты для '{product_name}':")
                for product_info in products:
                    print(
                        f"  {product_info['number']}. {product_info['brand']} {product_info['name'][:30]}... - {product_info['price']}")
            else:
                print(f"Для товара '{product_name}' не найдено результатов")

            if idx < len(products_list):
                print("\nПауза перед следующим запросом...")
                time.sleep(3)

        # Итоговая статистика
        print("\n" + "="*60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("="*60)
        print(f"Обработано товаров: {len(products_list)}")
        print(f"Всего спарсено карточек: {len(all_results)}")
        print(f"Результаты сохранены в: {CSV_FILE_PATH}")

        input("\nНажмите Enter для закрытия браузера...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
