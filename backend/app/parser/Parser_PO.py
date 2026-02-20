"""
Парсер реестра отечественного ПО (reestr.digital.gov.ru).
Парсит данные о программном обеспечении по поисковому запросу.
"""

import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import time
from urllib.parse import quote_plus

BASE_URL = "https://reestr.digital.gov.ru/import-substitution/"

# Путь к CSV (относительно корня проекта Kursach)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CSV_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "reestr_po.csv"


def get_software_list():
    """
    Получает список названий ПО от пользователя.
    
    Returns:
        list: список названий ПО для поиска
    """
    print("\nВведите названия ПО для поиска (по одному на строку).")
    print("Для завершения ввода введите пустую строку или 'stop':")

    software_list = []
    while True:
        software = input(f"ПО {len(software_list) + 1}: ").strip()
        if not software or software.lower() == "stop":
            break
        if software:
            software_list.append(software)

    return software_list


def parse_search_results(html_content, max_items):
    """
    Парсит HTML страницы с результатами поиска.
    
    Args:
        html_content (str): HTML содержимое страницы
        max_items (int): максимальное количество записей для парсинга
        
    Returns:
        list: список словарей с данными о ПО
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Находим все элементы с классом "item collection-item a-link"
    items = soup.find_all('div', class_='item collection-item a-link')
    
    print(f"Найдено записей на странице: {len(items)}")
    
    # Ограничиваем количество обрабатываемых записей
    items_to_parse = items[:max_items]
    
    for idx, item in enumerate(items_to_parse, 1):
        try:
            software_data = {}
            
            # Извлекаем дату регистрации
            date_elem = item.find('div', {'data-name': 'Дата регистрации'})
            if date_elem:
                date_span = date_elem.find('span')
                software_data['registration_date'] = date_span.text.strip() if date_span else ""
            else:
                software_data['registration_date'] = ""
            
            # Извлекаем наименование ПО
            name_elem = item.find('div', {'data-name': 'Наименование ПО'})
            if name_elem:
                software_data['software_name'] = name_elem.text.strip()
            else:
                software_data['software_name'] = ""
            
            # Добавляем номер записи для отслеживания
            software_data['number'] = idx
            
            if software_data['software_name']:  # Добавляем только если есть название
                results.append(software_data)
                print(f"  [{idx}] {software_data['software_name'][:60]}... | {software_data['registration_date']}")
            else:
                print(f"  [{idx}] Пропущено (нет названия)")
                
        except Exception as e:
            print(f"  Ошибка при парсинге записи {idx}: {e}")
            continue
    
    return results


def search_software(software_name, max_items=10):
    """
    Выполняет поиск ПО на сайте реестра.
    
    Args:
        software_name (str): название ПО для поиска
        max_items (int): максимальное количество записей для парсинга
        
    Returns:
        list: список словарей с данными о ПО
    """
    print(f"\n{'='*60}")
    print(f"Поиск: {software_name}")
    print(f"{'='*60}")
    
    # Формируем URL с поисковым запросом
    # Кодируем название ПО для URL (заменяем пробелы на +)
    encoded_query = quote_plus(software_name)
    search_url = f"{BASE_URL}?query=+{encoded_query}"
    
    print(f"URL: {search_url}")
    
    try:
        # Отправляем GET запрос
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"Статус ответа: {response.status_code}")
        
        # Парсим HTML
        results = parse_search_results(response.text, max_items)
        
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return []
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        return []


def save_to_csv(software_list, search_query):
    """
    Сохраняет результаты в CSV файл.
    
    Args:
        software_list (list): список словарей с данными о ПО
        search_query (str): поисковый запрос
    """
    if not software_list:
        print("Нет данных для сохранения в CSV")
        return

    CSV_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = CSV_FILE_PATH.is_file()
    fieldnames = ['search_query', 'number', 'registration_date', 'software_name']

    with open(str(CSV_FILE_PATH), 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        
        if not file_exists:
            writer.writeheader()
        
        for software in software_list:
            row = {
                'search_query': search_query,
                'number': software.get('number', ''),
                'registration_date': software.get('registration_date', ''),
                'software_name': software.get('software_name', '')
            }
            writer.writerow(row)

    print(f"\nРезультаты для '{search_query}' сохранены в CSV: {CSV_FILE_PATH}")


def main():
    print("\n" + "="*60)
    print("ПАРСЕР РЕЕСТРА ОТЕЧЕСТВЕННОГО ПО")
    print("reestr.digital.gov.ru")
    print("="*60)
    
    # Получаем список ПО для поиска
    software_names = get_software_list()
    
    if not software_names:
        print("Список ПО пуст. Программа завершена.")
        return
    
    print(f"\nБудет обработано ПО: {len(software_names)}")
    for i, name in enumerate(software_names, 1):
        print(f"  {i}. {name}")
    
    # Запрашиваем количество строк для парсинга
    max_items_input = input(
        "\nСколько записей парсить для каждого ПО (по умолчанию 10): "
    )
    max_items = int(max_items_input or "10")
    
    print(f"\nНачинаем обработку {len(software_names)} запросов...")
    print(f"Для каждого запроса будет спарсено до {max_items} записей\n")
    
    all_results = []
    
    try:
        for idx, software_name in enumerate(software_names, 1):
            print(f"\n[{idx}/{len(software_names)}] Обработка ПО...")
            
            # Выполняем поиск и парсинг
            results = search_software(software_name, max_items)
            
            if results:
                save_to_csv(results, software_name)
                all_results.extend(results)
                
                print(f"\nНайдено записей для '{software_name}': {len(results)}")
            else:
                print(f"Для '{software_name}' не найдено результатов.")
            
            # Пауза между запросами, чтобы не перегружать сервер
            if idx < len(software_names):
                print("\nПауза перед следующим запросом...")
                time.sleep(2)
        
        # Итоговая статистика
        print("\n" + "="*60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("="*60)
        print(f"Обработано запросов: {len(software_names)}")
        print(f"Всего записей сохранено: {len(all_results)}")
        print(f"Файл: {CSV_FILE_PATH}")
        
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
    except Exception as e:
        print(f"\nОшибка: {e}")


if __name__ == "__main__":
    main()
