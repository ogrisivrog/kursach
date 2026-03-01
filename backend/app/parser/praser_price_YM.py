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
import re

BASE_URL = "https://market.yandex.ru"
CSV_FILE_PATH = "/Users/denis/Desktop/Рабочий стол/ВУЗ/Романчева/Kursach/data/sellers/data_sellers.csv"


def get_browser():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=automation-controlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return uc.Chrome(version_main=144, options=options)


def apply_sorting(driver, wait, sort_type="price_asc"):
    """
    Применяет сортировку на Yandex Market
    """
    sort_options = {
        "price_asc": ["подешевле", "по возрастанию", "дешевые"],
        "price_desc": ["подороже", "по убыванию", "дорогие"],
        "popular": ["популярные", "по популярности"],
        "rating": ["высокий рейтинг", "по рейтингу"]
    }
    
    keywords = sort_options.get(sort_type, ["подешевле"])
    
    try:
        print("Пытаемся найти и открыть выпадающий список сортировки...")
        
        # СПОСОБ 1: Используем точный XPath, который вы нашли
        sort_button_xpath = "//*[@id='/content/page/fancyPage/searchContent/searchContentSync/searchControls/quickFiltersDsk/sort']/div[1]/button"
        
        try:
            sort_button = wait.until(EC.element_to_be_clickable((By.XPATH, sort_button_xpath)))
            print("Нашли кнопку сортировки по точному XPath")
        except:
            # Если не нашли по точному XPath, пробуем другие селекторы
            sort_selectors = [
                "//button[contains(@class, '_1fMqM')]",  # Класс кнопки сортировки в ЯМ
                "//button[contains(@class, 'sort')]",
                "//div[contains(@data-apiary-widget-name, 'Sort')]//button",
                "//span[contains(text(), 'Сортировка')]/..",
                "//button[contains(@aria-label, 'Сортировка')]",
                "//*[@data-auto='sort']//button",
                "//*[contains(@class, 'SortButton')]"
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
            print("Не удалось найти кнопку сортировки")
            return False
        
        # Прокручиваем к кнопке
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_button)
        time.sleep(1)
        
        # Кликаем по кнопке сортировки
        print("Кликаем на кнопку сортировки...")
        try:
            sort_button.click()
        except:
            driver.execute_script("arguments[0].click();", sort_button)
        time.sleep(2)
        
        # Ищем элементы выпадающего списка
        print("Ищем элементы сортировки...")
        
        item_selectors = [
            "//div[@data-apiary-widget-name='Sort']//li//span",
            "//*[@role='listbox']//*[@role='option']",
            "//li[contains(@class, '_1PpU_')]//span",
            "//div[contains(@class, 'menu')]//button",
            "//ul//span[contains(text(), 'шевле')]/..",
            "//ul//span[contains(text(), 'цен')]/..",
            "//span[contains(text(), 'подешевле')]/..",
            "//span[contains(text(), 'подороже')]/..",
            "//button[contains(@class, 'sort')]//span[contains(text(), 'шевле')]/.."
        ]
        
        sort_items = []
        for selector in item_selectors:
            try:
                items = driver.find_elements(By.XPATH, selector)
                if items:
                    sort_items = items
                    print(f"Нашли элементы списка по селектору: {selector}, всего: {len(items)}")
                    break
            except:
                continue
        
        if sort_items:
            print("Найденные варианты сортировки:")
            for item in sort_items:
                try:
                    text = item.text.strip()
                    if text and len(text) < 50:
                        print(f"  - {text}")
                except:
                    pass
            
            for item in sort_items:
                try:
                    item_text = item.text.lower()
                    print(f"Проверяем элемент: {item_text[:50]}...")
                    
                    for keyword in keywords:
                        if keyword.lower() in item_text:
                            print(f"Нашли нужный вариант: {item.text}")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                            time.sleep(0.5)
                            
                            try:
                                item.click()
                            except:
                                driver.execute_script("arguments[0].click();", item)
                            
                            print("Применили сортировку")
                            time.sleep(2)
                            return True
                except Exception as e:
                    continue
        
        print("Пробуем прямые XPath для сортировки 'подешевле'...")
        price_asc_xpaths = [
            "//span[contains(text(), 'подешевле')]/..",
            "//button//span[contains(text(), 'подешевле')]",
            "//*[contains(text(), 'подешевле')]",
            "//span[contains(text(), 'По возрастанию')]/..",
            "//*[@data-value='price_asc']",
            "//*[@data-autotest-id='price_asc']"
        ]
        
        for xpath in price_asc_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    element = elements[0]
                    print(f"Нашли элемент по XPath: {xpath}")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", element)
                    print("Применили сортировку")
                    time.sleep(2)
                    return True
            except:
                continue
        
        print("Пробуем JavaScript для выбора сортировки...")
        driver.execute_script("""
            let elements = document.querySelectorAll('span, button, div');
            for (let el of elements) {
                if (el.textContent && (
                    el.textContent.toLowerCase().includes('подешевле') || 
                    el.textContent.toLowerCase().includes('по возрастанию')
                )) {
                    console.log('Найден элемент:', el.textContent);
                    el.click();
                    break;
                }
            }
        """)
        time.sleep(2)
        
        try:
            button_text = sort_button.text.lower()
            if 'подешевле' in button_text or 'по возрастанию' in button_text:
                print("Сортировка успешно применена (проверено по тексту кнопки)")
                return True
        except:
            pass
        
        print("Не удалось применить сортировку")
        return False
        
    except Exception as e:
        print(f"Ошибка при сортировке: {e}")
        return False


def parse_product_cards_ym(driver, max_cards=10):
    """
    Парсит информацию с карточек товаров на Яндекс Маркете
    
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
        
        # Прокручиваем страницу для загрузки всех карточек
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Базовый XPath для контейнера с карточками
        base_container_xpath = "/html/body/div[2]/div/div[2]/div/div[1]/div/div[2]/div/div[4]/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div/div/div/div"
        
        try:
            # Находим контейнер с карточками
            container = driver.find_element(By.XPATH, base_container_xpath)
            print("Найден контейнер с карточками товаров")
            
            # Находим все div'ы внутри контейнера (кроме первого, который может быть не карточкой)
            all_divs = container.find_elements(By.XPATH, "./div")
            print(f"Всего div элементов в контейнере: {len(all_divs)}")
            
            # Фильтруем только те div'ы, которые содержат article (карточки товаров)
            product_cards = []
            for div in all_divs:
                try:
                    article = div.find_element(By.XPATH, "./article")
                    if article:
                        product_cards.append(article)
                        print(f"Найдена карточка товара с article")
                except:
                    continue
            
            # Если не нашли article, пробуем другой подход
            if not product_cards:
                # Ищем все article напрямую в контейнере
                product_cards = container.find_elements(By.XPATH, ".//article")
                print(f"Найдено article элементов: {len(product_cards)}")
            
        except Exception as e:
            print(f"Не удалось найти контейнер по точному XPath: {e}")
            
            # Запасной вариант: ищем все article на странице
            product_cards = driver.find_elements(By.XPATH, "//article")
            print(f"Найдено article элементов на всей странице: {len(product_cards)}")
        
        if not product_cards:
            print("Не удалось найти карточки товаров")
            return products
        
        print(f"Всего найдено карточек для парсинга: {len(product_cards)}")
        
        # Ограничиваем количество карточек
        cards_to_parse = product_cards[:max_cards]
        
        for i, card in enumerate(cards_to_parse, 1):
            try:
                product_info = {'number': i}
                print(f"\n--- Парсинг карточки {i} ---")
                
                # ПОЛУЧАЕМ НАЗВАНИЕ ТОВАРА
                name = None
                
                # Пробуем найти название в различных местах карточки
                name_xpaths = [
                    ".//h3//span",  # Часто название в h3
                    ".//a[contains(@href, '/product--')]//span",  # В ссылке на товар
                    ".//span[contains(@class, 'title')]",
                    ".//div[contains(@class, 'title')]",
                    ".//*[@data-auto='product-title']//span",
                    ".//a//span",  # Любой span внутри ссылки
                    ".//h3",  # Весь h3
                ]
                
                for xpath in name_xpaths:
                    try:
                        elements = card.find_elements(By.XPATH, xpath)
                        for elem in elements:
                            text = elem.text.strip()
                            # Название должно быть достаточно длинным и не содержать цену
                            if text and len(text) > 10 and '₽' not in text:
                                name = text
                                print(f"  Название найдено: {text[:50]}...")
                                break
                        if name:
                            break
                    except:
                        continue
                
                # Если не нашли, пробуем взять первый длинный текст из карточки
                if not name:
                    try:
                        all_text = card.text.strip().split('\n')
                        # Ищем строку, которая выглядит как название (длинная, без цены)
                        for line in all_text:
                            if len(line) > 15 and '₽' not in line and not line.replace(' ', '').isdigit():
                                name = line
                                print(f"  Название найдено из текста: {line[:50]}...")
                                break
                    except:
                        pass
                
                product_info['name'] = name if name else "Не указано"
                
                # ПОЛУЧАЕМ ЦЕНУ
                price = None
                
                price_xpaths = [
                    ".//span[contains(@class, 'price')]//span//span",
                    ".//*[@data-auto='price']//span",
                    ".//div[contains(@class, 'price')]//span",
                    ".//a[contains(@class, 'price')]//span",
                    ".//span[contains(@class, '_3na6s')]",
                    ".//*[contains(text(), '₽')]",
                    ".//span[contains(@class, 'Currency')]/..",
                    ".//span[contains(@class, 'price')]"
                ]
                
                for xpath in price_xpaths:
                    try:
                        elements = card.find_elements(By.XPATH, xpath)
                        for elem in elements:
                            text = elem.text.strip()
                            if text and '₽' in text:
                                # Очищаем цену от символов валюты и пробелов
                                price_clean = ''.join(c for c in text if c.isdigit() or c in '.,')
                                if price_clean:
                                    price = price_clean
                                    print(f"  Цена найдена: {text}")
                                    break
                        if price:
                            break
                    except:
                        continue
                
                # Если не нашли по селекторам, ищем по регулярному выражению
                if not price:
                    try:
                        card_text = card.text
                        # Ищем паттерн цены (цифры с пробелами и ₽)
                        price_pattern = r'(\d[\d\s]*\d)\s*₽'
                        match = re.search(price_pattern, card_text)
                        if match:
                            price = match.group(1).replace(' ', '')
                            print(f"  Цена найдена через regex: {price}")
                    except:
                        pass
                
                product_info['price'] = price if price else "Цена не указана"
                
                # ПОЛУЧАЕМ БРЕНД (обычно первое слово в названии или отдельный элемент)
                brand = None
                
                brand_xpaths = [
                    ".//span[contains(@class, 'brand')]",
                    ".//div[contains(@class, 'brand')]",
                    ".//*[@data-auto='brand']",
                    ".//span[contains(@class, 'vendor')]"
                ]
                
                for xpath in brand_xpaths:
                    try:
                        elements = card.find_elements(By.XPATH, xpath)
                        if elements:
                            brand = elements[0].text.strip()
                            print(f"  Бренд найден отдельно: {brand}")
                            break
                    except:
                        continue
                
                # Если бренд не найден отдельно, берем первое слово из названия
                if not brand and product_info['name'] != "Не указано":
                    words = product_info['name'].split()
                    if words and len(words[0]) > 1:
                        brand = words[0]
                        print(f"  Бренд взят из названия: {brand}")
                
                product_info['brand'] = brand if brand else "Не указан"
                
                # ПОЛУЧАЕМ ССЫЛКУ НА ТОВАР
                link = None
                
                link_xpaths = [
                    ".//a[contains(@href, '/product--')]",
                    ".//a[@data-auto='product-title']",
                    ".//h3/a",
                    ".//a"
                ]
                
                for xpath in link_xpaths:
                    try:
                        elements = card.find_elements(By.XPATH, xpath)
                        if elements:
                            link = elements[0].get_attribute('href')
                            if link and ('/product--' in link or '/offer/' in link):
                                print(f"  Ссылка найдена")
                                break
                    except:
                        continue
                
                product_info['link'] = link if link else None
                
                products.append(product_info)
                print(f"  ИТОГ Карточка {i}:")
                print(f"    Бренд: {product_info['brand']}")
                print(f"    Название: {product_info['name'][:50]}...")
                print(f"    Цена: {product_info['price']}")
                print(f"    Ссылка: {product_info['link']}")
                
            except Exception as e:
                print(f"Ошибка при парсинге карточки {i}: {e}")
                continue
        
        print(f"\nУспешно спарсено карточек: {len(products)} из {max_cards}")
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
    
    print(f"Результаты для '{search_query}' добавлены в CSV файл: {CSV_FILE_PATH}")


def search_and_parse_product(driver, wait, product_name, max_cards):
    """
    Выполняет поиск и парсинг для одного товара
    
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
    
    # --- поиск ---
    print("Выполняем поиск...")
    try:
        # Ищем поле поиска
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "header-search"))
        )
        
        # Очищаем поле и вводим новый запрос
        search_input.click()
        search_input.clear()
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
    products = parse_product_cards_ym(driver, max_cards)
    
    return products


def get_products_list():
    """
    Получает список товаров от пользователя
    
    Returns:
        list: список названий товаров
    """
    print("\nВведите названия товаров для поиска (по одному на строку).")
    print("Для завершения ввода введите пустую строку или 'stop':")
    
    products = ["iphone 14 pro max", "iphone 17 pro max"]
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
    print("ПАРСЕР ЯНДЕКС МАРКЕТ - ПАКЕТНАЯ ОБРАБОТКА")
    print("="*60)
    
    # Получаем список товаров
    products_list = get_products_list()
    
    if not products_list:
        print("Список товаров пуст. Программа завершена.")
        return
    
    print(f"\nБудет обработано товаров: {len(products_list)}")
    for i, product in enumerate(products_list, 1):
        print(f"  {i}. {product}")
    
    # max_cards = int(input("\nСколько карточек спарсить для каждого товара (по умолчанию 10): ") or "10")
    max_cards = 3
    
    print(f"\nНачинаем обработку {len(products_list)} товаров...")
    
    driver = get_browser()
    wait = WebDriverWait(driver, 20)
    
    try:
        # Открываем главную страницу один раз
        driver.get(BASE_URL)
        time.sleep(5)
        
        all_results = []
        
        # Обрабатываем каждый товар
        for idx, product_name in enumerate(products_list, 1):
            print(f"\n[{idx}/{len(products_list)}] Обработка товара...")
            
            products = search_and_parse_product(driver, wait, product_name, max_cards)
            
            if products:
                # Сохраняем результаты в CSV (добавляем к существующему файлу)
                save_to_csv(products, product_name)
                all_results.extend(products)
                
                # Выводим краткие результаты
                print(f"\nРезультаты для '{product_name}':")
                for product_info in products:
                    print(f"  {product_info['number']}. {product_info['brand']} {product_info['name'][:30]}... - {product_info['price']}")
            else:
                print(f"Для товара '{product_name}' не найдено результатов")
            
            # Небольшая пауза между запросами
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
        
        # держим браузер открытым
        input("\nНажмите Enter для закрытия браузера...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()