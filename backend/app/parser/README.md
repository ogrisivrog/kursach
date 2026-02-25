## Парсеры в `backend/app/parser`

### Маркетплейсы (Wildberries + Яндекс.Маркет)

- **parser_price_WB.py** — парсер Wildberries (консольный, с вводом товаров).
- **praser_price_YM.py** — парсер Яндекс.Маркета (консольный, с вводом товаров).
- **parser_unified.py** — единая программа, которая по одному списку товаров:
  - парсит WB и Я.Маркет,
  - объединяет результаты,
  - сохраняет **топ‑3 самых дешёвых** карточек по каждому запросу.

**Запуск единой программы:**

Из корня проекта:
```bash
python -m backend.app.parser.parser_unified
```

Из папки `backend/app/parser`:
```bash
python parser_unified.py
```

**Формат CSV (`data/sellers/data_sellers.csv`) для `parser_unified.py`:**

- `search_query` — поисковый запрос;
- `number` — порядковый номер в топ‑3 (1–3);
- `brand`, `name`, `price`, `link`;
- `marketplace` — `Wildberries` или `Яндекс.Маркет`.

---

### Реестр отечественного ПО (`reestr.digital.gov.ru`)

- **Parser_PO.py** — парсер реестра отечественного ПО.

Функция верхнего уровня:

```python
from backend.app.parser.Parser_PO import parse_reestr_po

software_list = ["Cisco", "Oracle"]
max_items = 5

json_rows = parse_reestr_po(software_list, max_items)
```

**Что делает:**
- формирует ссылки вида  
  `https://reestr.digital.gov.ru/import-substitution/?query=+Cisco`;
- для каждой записи берёт:
  - `registration_date` — дата регистрации;
  - `software_name` — наименование ПО;
  - `number` — порядковый номер в выдаче;
  - `search_query` — исходный запрос;
- возвращает **список JSON‑строк** (каждая строка — один объект).

В терминал выводится краткий лог: сколько запросов, сколько записей по каждому, итоговое количество.

---

### Robotbaza (`robotbaza.ru`)

- **Parser_RobotoBaza.py** — парсер поиска по `robotbaza.ru`.

Пример использования:

```python
from backend.app.parser.Parser_RobotoBaza import parse_robotbaza

products = ["микросхема", "Arduino"]
max_items = 3

rows = parse_robotbaza(products, max_items)
```

**Что делает:**
- отправляет запросы вида  
  `https://robotbaza.ru/search?q=микросхема`;
- по каждой карточке берёт:
  - `product_name` — название товара;
  - `price` — цена (из JSON товара, чтобы обойти JS‑подгрузку);
  - `url` — ссылка на карточку;
  - `number` — порядковый номер;
  - `search_query` — исходный запрос.

Возвращает список словарей; в терминал печатает прогресс по запросам.

---

### Fgoskomplekt (`fgoskomplekt.ru`)

- **Parser_Komplekt.py** — парсер каталога `fgoskomplekt.ru` по строке поиска.

Поисковая ссылка:

```text
https://fgoskomplekt.ru/catalog/?faction_type=variant&faction_word=&faction_site=variant2&q=RS+232&type=catalog&s=Найти
```

Пример использования:

```python
from backend.app.parser.Parser_Komplekt import parse_komplekt

products = ["RS 232", "Arduino"]
rows = parse_komplekt(products, max_items=5)
```

**Что делает:**
- формирует запрос с параметром `q` (пробелы в названии автоматически кодируются как `+`);
- из карточек выдачи берёт:
  - `product_name` — название (`<span>RS-232 Shield</span>` и т.п.);
  - `price` — цена из  
    `span.price__new-val font_16 font_14--to-600` (строкой, например `"1909.60"`);
  - `url` — полная ссылка на товар;
  - `number` — порядковый номер;
  - `search_query` — исходный запрос.

Возвращает список словарей и печатает краткий ход работы в терминал.

