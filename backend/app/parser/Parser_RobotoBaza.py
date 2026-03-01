"""
Парсер сайта robotbaza.ru (поиск товаров).
Ищет товары по запросу и вытаскивает название и цену из карточек.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Optional

BASE_URL = "https://robotbaza.ru/search"
SITE_ORIGIN = "https://robotbaza.ru"


def _price_to_digits(price_value) -> str:
    if price_value is None:
        return ""
    s = str(price_value).strip()
    if not s:
        return ""
    if "." in s:
        s = s.split(".", 1)[0]
    return "".join(ch for ch in s if ch.isdigit())


def _fetch_price_via_product_json(session: requests.Session, product_path: str) -> str:
    """
    Цена в поисковой выдаче часто подгружается JS.
    Но она доступна по JSON-эндпоинту товара:
    https://robotbaza.ru/product/<slug>.json
    """
    if not product_path:
        return ""

    json_url = f"{SITE_ORIGIN}{product_path}.json"
    try:
        r = session.get(json_url, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return ""

    product = (data or {}).get("product") or {}

    variants = product.get("variants") or []
    if variants and isinstance(variants, list):
        digits = _price_to_digits((variants[0] or {}).get("price"))
        if digits:
            return digits

    return _price_to_digits(product.get("price_min"))


def _parse_product_cards(html: str, max_items: int, session: Optional[requests.Session] = None):
    """
    Парсит HTML страницы поиска Robotbaza и достаёт карточки товаров.

    Возвращает список словарей с полями:
    - number: порядковый номер в выдаче (1..)
    - product_name: название товара
    - price: цена (строкой с цифрами, без пробелов и валюты)
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # Карточки товара - это <form class="card ...">
    cards = soup.select("form.card")

    cards_to_parse = cards[:max_items]

    for idx, card in enumerate(cards_to_parse, start=1):
        try:
            # Название товара
            name_el = card.select_one(".info .name-wrap a.name")
            product_name = name_el.get_text(strip=True) if name_el else ""
            product_href = name_el.get("href") if name_el else ""

            # Цена: берём через JSON товара (в HTML выдачи её может не быть)
            price_digits = ""
            if session and product_href:
                price_digits = _fetch_price_via_product_json(session, product_href)

            if not product_name:
                continue

            results.append(
                {
                    "number": idx,
                    "product_name": product_name,
                    "price": price_digits,
                    "url": f"{SITE_ORIGIN}{product_href}" if product_href else "",
                }
            )
        except Exception:
            continue

    return results


def search_robotbaza(product_name: str, max_items: int = 10):
    """
    Выполняет поиск по одному запросу на robotbaza.ru
    и возвращает список карточек (dict) с названием и ценой.
    """
    params = {"q": product_name}
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    )

    try:
        resp = session.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка запроса для «{product_name}»: {e}")
        return []

    items = _parse_product_cards(resp.text, max_items, session=session)
    return items


def parse_robotbaza(product_names, max_items: int = 10):
    """
    Основная функция парсинга Robotbaza.

    Args:
        product_names (list[str]): список названий товаров для поиска
        max_items (int): максимум карточек на каждый запрос (если на сайте меньше – берём сколько есть)

    Returns:
        list[dict]: список словарей с полями:
            - search_query
            - number
            - product_name
            - price
    """
    all_results = []

    print(
        f"Парсер Robotbaza: запросов={len(product_names)}, карточек на запрос={max_items}"
    )

    for i, name in enumerate(product_names, start=1):
        print(f"  [{i}/{len(product_names)}] Поиск: «{name}»...", end=" ")
        items = search_robotbaza(name, max_items=max_items)

        # добавляем поле search_query к каждому результату
        for item in items:
            item["search_query"] = name

        all_results.extend(items)
        print(f"найдено {len(items)} карточек")

        if i < len(product_names):
            time.sleep(1.5)

    print(f"Итого: {len(all_results)} карточек по всем запросам.")
    return all_results


if __name__ == "__main__":
    # Пример ручного запуска/теста
    test_products = ["микросхема", "Arduino", "робот"]
    data = parse_robotbaza(test_products, max_items=3)
    for row in data:
        print(row)

