# Парсеры цен с маркетплейсов

## Файлы

- **parser_price_WB.py** — парсер Wildberries (отдельный запуск)
- **praser_price_YM.py** — парсер Яндекс.Маркета (отдельный запуск)
- **parser_unified.py** — единая программа: парсит оба маркетплейса и сохраняет топ-3 товара с самыми низкими ценами

## Запуск единой программы

Из корня проекта:
```bash
python -m backend.app.parser.parser_unified
```

Из папки `backend/app/parser`:
```bash
python parser_unified.py
```

## Формат CSV

При использовании `parser_unified.py` в файл `data/sellers/data_sellers.csv` записываются:
- search_query — поисковый запрос
- number — порядковый номер (1–3)
- brand, name, price, link
- marketplace — Wildberries или Яндекс.Маркет
