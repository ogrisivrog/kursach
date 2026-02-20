"""
Парсер реестра отечественного ПО (reestr.digital.gov.ru).
Парсит данные о программном обеспечении по поисковому запросу.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote_plus

BASE_URL = "https://reestr.digital.gov.ru/import-substitution/"


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
                
        except Exception:
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
    # Формируем URL с поисковым запросом
    encoded_query = quote_plus(software_name)
    search_url = f"{BASE_URL}?query=+{encoded_query}"
    
    try:
        # Отправляем GET запрос
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Парсим HTML
        results = parse_search_results(response.text, max_items)
        
        return results
        
    except Exception:
        return []


def parse_reestr_po(software_names, max_items=10):
    """
    Основная функция парсинга реестра ПО.
    
    Args:
        software_names (list): список названий ПО для поиска
        max_items (int): максимальное количество записей для парсинга каждого ПО
        
    Returns:
        list: список JSON-строк (каждая строка - JSON объект с данными о ПО)
    """
    all_results = []

    print(f"Парсер реестра ПО: запросов={len(software_names)}, записей на запрос={max_items}")

    for i, software_name in enumerate(software_names, 1):
        print(f"  [{i}/{len(software_names)}] Поиск: «{software_name}»...", end=" ")
        results = search_software(software_name, max_items)

        for result in results:
            result['search_query'] = software_name
        all_results.extend(results)

        print(f"найдено {len(results)} записей")
        time.sleep(2)

    json_results = [json.dumps(r, ensure_ascii=False) for r in all_results]
    print(f"Итого: {len(json_results)} записей, возвращаю список JSON-строк.")
    return json_results

software_names = ["Cisco", "Oracle"]
max_items = 3

print(parse_reestr_po(software_names, max_items))