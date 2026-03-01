"""
Парсер сайта fgoskomplekt.ru (поиск товаров).
Ищет товары по запросу и вытаскивает название, цену и ссылку из карточек.

Пример поисковой ссылки:
https://fgoskomplekt.ru/catalog/?faction_type=variant&faction_word=&faction_site=variant2&q=RS+232&type=catalog&s=Найти
"""

import time
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://fgoskomplekt.ru/catalog/"
SITE_ORIGIN = "https://fgoskomplekt.ru"


def _price_text_to_digits(raw_price: str) -> str:
    """
    Преобразует строку вида '1 909.60 ₽' -> '1909.60' (или '1909').
    Для дальнейшей обработки можно приводить к float.
    """
    if not raw_price:
        return ""
    # Убираем неразрывные пробелы и символ валюты
    cleaned = raw_price.replace("\xa0", " ").replace("₽", "").strip()
    # Оставляем только цифры, точку и запятую
    allowed = "".join(ch for ch in cleaned if ch.isdigit() or ch in ".,")
    # Заменяем запятую на точку
    allowed = allowed.replace(",", ".")
    return allowed


def _parse_product_cards(html: str, max_items: int) -> List[Dict]:
    """
    Парсит HTML страницы поиска fgoskomplekt.ru и достаёт карточки товаров.

    Возвращает список словарей с полями:
    - number: порядковый номер в выдаче (1..)
    - product_name: название товара
    - price: цена строкой (например '1909.60')
    - url: полная ссылка на карточку товара
    """
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict] = []

    # Ищем все элементы с ценой
    # <span class="price__new-val font_16 font_14--to-600">1 909.60 ₽</span>
    price_spans = soup.select("span.price__new-val")

    for idx, price_el in enumerate(price_spans[:max_items], start=1):
        try:
            # Цена
            raw_price = price_el.get_text(" ", strip=True)
            price_str = _price_text_to_digits(raw_price)

            # Пробуем найти контейнер карточки: поднимаемся вверх несколько уровней,
            # пока не встретим что-то, где есть текст "В корзину"
            card = price_el
            for _ in range(6):
                if card is None:
                    break
                if card.find(string=lambda t: isinstance(t, str) and "В корзину" in t):
                    break
                card = card.parent
            if card is None:
                card = price_el.parent

            # Название товара: в карточке ищем подходящий span или ссылку
            product_name = ""
            name_el = None

            # сначала пробуем найти ссылку, у которой есть текст
            link_el = card.find("a")
            if link_el and link_el.get_text(strip=True):
                name_el = link_el
            else:
                # fallback: первый span с текстом без '₽', 'Наличие', 'В корзину'
                for span in card.find_all("span"):
                    text = span.get_text(strip=True)
                    if not text:
                        continue
                    if "₽" in text:
                        continue
                    if "Наличие" in text or "В корзину" in text:
                        continue
                    name_el = span
                    break

            if name_el:
                product_name = name_el.get_text(strip=True)

            # Ссылка на товар
            url = ""
            link = name_el.find_parent("a") if name_el else None
            if not link:
                link = card.find("a")
            if link and link.get("href"):
                href = link.get("href")
                url = href if href.startswith(
                    "http") else f"{SITE_ORIGIN}{href}"

            if not product_name:
                continue

            results.append(
                {
                    "number": idx,
                    "product_name": product_name,
                    "price": price_str,
                    "url": url,
                }
            )
        except Exception:
            continue

    return results


def search_komplekt(product_name: str, max_items: int = 10) -> List[Dict]:
    """
    Выполняет поиск по одному запросу на fgoskomplekt.ru
    и возвращает список карточек с названием, ценой и ссылкой.
    """
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

    params = {
        "faction_type": "variant",
        "faction_word": "",
        "faction_site": "variant2",
        "q": product_name,
        "type": "catalog",
        "s": "Найти",
    }

    try:
        resp = session.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка запроса для «{product_name}»: {e}")
        return []

    return _parse_product_cards(resp.text, max_items)


def parse_komplekt(product_names: List[str], max_items: int = 10) -> List[Dict]:
    """
    Основная функция: принимает список товаров и возвращает список карточек.

    Каждому результату добавляется поле search_query с исходным запросом.
    """
    all_results: List[Dict] = []

    print(
        f"Парсер fgoskomplekt: запросов={len(product_names)}, карточек на запрос={max_items}"
    )

    for i, name in enumerate(product_names, start=1):
        print(f"  [{i}/{len(product_names)}] Поиск: «{name}»...", end=" ")
        items = search_komplekt(name, max_items=max_items)

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
    test_products = ["RS 232", "Микросхема"]
    data = parse_komplekt(test_products, max_items=3)
    for row in data:
        print(row)
