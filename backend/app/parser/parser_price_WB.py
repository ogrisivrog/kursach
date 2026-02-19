import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from datetime import datetime
import json
import csv
import os

BASE_URL = "https://www.wildberries.ru"


def get_browser():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=automation-controlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return uc.Chrome(version_main=144, options=options)


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
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_button)
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
                    print(f"Нашли элементы списка по селектору: {selector}, всего: {len(items)}")
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
                        print(f"Нашли элементы списка по CSS: {selector}, всего: {len(items)}")
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
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                            time.sleep(0.5)
                            driver.execute_script("arguments[0].click();", item)
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
                element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
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
                        alt_brand = card.find_elements(By.XPATH, alt_brand_xpath)
                        if alt_brand:
                            brand_text = alt_brand[0].text.strip()
                            product_info['brand'] = brand_text if brand_text else "Не указан"
                        else:
                            product_info['brand'] = "Не указан"
                except Exception as e:
                    product_info['brand'] = "Не указан"
                    print(f"  Ошибка при получении бренда для карточки {i}: {e}")
                
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
                            name_text = name_elements[0].text.strip()
                            if name_text and len(name_text) > 3:
                                break
                    
                    product_info['name'] = name_text if name_text else "Не указано"
                except Exception as e:
                    product_info['name'] = "Не указано"
                    print(f"  Ошибка при получении названия для карточки {i}: {e}")
                
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
                                price_text = ''.join(c for c in price_text if c.isdigit() or c in '.,')
                                break
                    
                    product_info['price'] = price_text if price_text else "Цена не указана"
                except Exception as e:
                    product_info['price'] = "Цена не указана"
                    print(f"  Ошибка при получении цены для карточки {i}: {e}")
                
                # Добавляем номер карточки
                product_info['number'] = i
                
                products.append(product_info)
                print(f"  Карточка {i}: {product_info.get('brand', '')} {product_info.get('name', '')[:50]}... - {product_info.get('price', '')}")
                
            except Exception as e:
                print(f"Ошибка при парсинге карточки {i}: {e}")
                continue
        
        return products
        
    except Exception as e:
        print(f"Ошибка при парсинге карточек: {e}")
        return products


def save_to_json(products, search_query):
    """
    Сохраняет результаты в JSON файл
    
    Args:
        products (list): список словарей с информацией о товарах
        search_query (str): поисковый запрос
    """
    if not products:
        print("Нет данных для сохранения в JSON")
        return
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wildberries_{search_query}_{timestamp}.json"
    
    # Подготавливаем данные для сохранения
    data = {
        "search_query": search_query,
        "timestamp": datetime.now().isoformat(),
        "total_products": len(products),
        "products": products
    }
    
    # Сохраняем в JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Результаты сохранены в JSON файл: {filename}")


def save_to_csv(products, search_query):
    """
    Сохраняет результаты в CSV файл
    
    Args:
        products (list): список словарей с информацией о товарах
        search_query (str): поисковый запрос
    """
    if not products:
        print("Нет данных для сохранения в CSV")
        return
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wildberries_{search_query}_{timestamp}.csv"
    
    # Определяем заголовки
    fieldnames = ['number', 'brand', 'name', 'price', 'link']
    
    # Сохраняем в CSV
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for product in products:
            # Преобразуем для CSV
            row = {
                'number': product.get('number', ''),
                'brand': product.get('brand', ''),
                'name': product.get('name', ''),
                'price': product.get('price', ''),
                'link': product.get('link', '')
            }
            writer.writerow(row)
    
    print(f"Результаты сохранены в CSV файл: {filename}")


def save_to_excel(products, search_query):
    """
    Сохраняет результаты в Excel файл
    
    Args:
        products (list): список словарей с информацией о товарах
        search_query (str): поисковый запрос
    """
    if not products:
        print("Нет данных для сохранения в Excel")
        return
    
    # Создаем DataFrame
    df = pd.DataFrame(products)
    
    # Переупорядочиваем колонки
    columns_order = ['number', 'brand', 'name', 'price', 'link']
    df = df[columns_order]
    
    # Переименовываем колонки для читаемости
    df.columns = ['№', 'Производитель', 'Название', 'Цена', 'Ссылка']
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"wildberries_{search_query}_{timestamp}.xlsx"
    
    # Сохраняем в Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Товары', index=False)
        
        # Настраиваем ширину колонок
        worksheet = writer.sheets['Товары']
        worksheet.column_dimensions['A'].width = 8   # №
        worksheet.column_dimensions['B'].width = 25  # Производитель
        worksheet.column_dimensions['C'].width = 60  # Название
        worksheet.column_dimensions['D'].width = 15  # Цена
        worksheet.column_dimensions['E'].width = 50  # Ссылка
    
    print(f"Результаты сохранены в Excel файл: {filename}")


def save_all_formats(products, search_query):
    """
    Сохраняет результаты во всех форматах (JSON, CSV, Excel)
    
    Args:
        products (list): список словарей с информацией о товарах
        search_query (str): поисковый запрос
    """
    if not products:
        print("Нет данных для сохранения")
        return
    
    print("\n" + "="*50)
    print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*50)
    
    # Создаем папку для результатов, если её нет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"results_{search_query}_{timestamp}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Создана папка: {folder_name}")
    
    # Сохраняем оригинальные пути
    original_cwd = os.getcwd()
    
    try:
        # Переходим в папку с результатами
        os.chdir(folder_name)
        
        # Сохраняем в разных форматах
        save_to_json(products, search_query)
        save_to_csv(products, search_query)
        save_to_excel(products, search_query)
        
        print(f"\nВсе файлы сохранены в папке: {folder_name}")
        
    finally:
        # Возвращаемся в исходную папку
        os.chdir(original_cwd)


def parse_single_card_with_given_xpaths(driver, card_number=1):
    """
    Парсит одну карточку товара по указанным XPath путям
    
    Args:
        driver: экземпляр веб-драйвера
        card_number (int): номер карточки (начиная с 1)
        
    Returns:
        dict: информация о товаре
    """
    product = {}
    
    try:
        # Базовый XPath для карточки
        base_xpath = f"/html/body/div[2]/main/div[2]/div[1]/div/div[1]/div/div/div[4]/div[1]/div/div/article[{card_number}]"
        
        # Получаем производителя (может отсутствовать)
        try:
            brand_xpath = f"{base_xpath}/div/div[3]/h2/span[1]"
            brand_element = driver.find_element(By.XPATH, brand_xpath)
            product['brand'] = brand_element.text.strip()
        except:
            product['brand'] = "Не указан"
            print(f"Производитель не найден для карточки {card_number}")
        
        # Получаем название товара
        try:
            name_xpath = f"{base_xpath}/div/div[3]/h2/span[2]"
            name_element = driver.find_element(By.XPATH, name_xpath)
            product['name'] = name_element.text.strip()
        except Exception as e:
            product['name'] = "Не указано"
            print(f"Ошибка при получении названия для карточки {card_number}: {e}")
        
        # Получаем цену
        try:
            price_xpath = f"{base_xpath}/div/div[3]/div/span[1]/span/ins"
            price_element = driver.find_element(By.XPATH, price_xpath)
            price_text = price_element.text.strip()
            # Очищаем цену от символов валюты
            product['price'] = ''.join(c for c in price_text if c.isdigit() or c in '.,')
        except Exception as e:
            product['price'] = "Цена не указана"
            print(f"Ошибка при получении цены для карточки {card_number}: {e}")
        
        # Получаем ссылку на товар
        try:
            link_xpath = f"{base_xpath}/div/a"
            link_element = driver.find_element(By.XPATH, link_xpath)
            product['link'] = link_element.get_attribute('href')
        except:
            try:
                link_xpath = f"{base_xpath}/a"
                link_element = driver.find_element(By.XPATH, link_xpath)
                product['link'] = link_element.get_attribute('href')
            except:
                product['link'] = None
        
        product['number'] = card_number
        
    except Exception as e:
        print(f"Ошибка при парсинге карточки {card_number}: {e}")
    
    return product


def main():
    product = input("Введите товар для поиска: ")
    max_cards = int(input("Сколько карточек спарсить (по умолчанию 10): ") or "10")

    driver = get_browser()
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get(BASE_URL)
        time.sleep(2)

        # --- поиск ---
        print("Выполняем поиск...")
        search_input = wait.until(
            EC.presence_of_element_located((By.ID, "searchInput"))
        )
        search_input.click()
        search_input.clear()
        search_input.send_keys(product)
        time.sleep(1)
        search_input.send_keys(Keys.ENTER)

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
        
        # Выводим результаты
        print("\n" + "="*80)
        print("РЕЗУЛЬТАТЫ ПАРСИНГА:")
        print("="*80)
        for product_info in products:
            print(f"\nКарточка №{product_info['number']}")
            print(f"Производитель: {product_info.get('brand', 'Не указан')}")
            print(f"Название: {product_info.get('name', 'Не указано')}")
            print(f"Цена: {product_info.get('price', 'Не указана')}")
            print(f"Ссылка: {product_info.get('link', 'Не указана')}")
        
        # Сохраняем во всех форматах
        save_all_formats(products, product)
        
        # держим браузер открытым
        input("\nНажмите Enter для закрытия браузера...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()