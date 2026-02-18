# MTO (minimal start)

## Что есть сейчас
- PostgreSQL (docker)
- FastAPI backend (docker)
- Таблицы: `items`, `locations`, `inventory`
- Импорт CSV в БД:
  - `POST /import/inventory` (загрузить файл)
  - `POST /import/inventory-from-path` (взять CSV из `./data`)
- Просмотр:
  - `GET /inventory`
  - `GET /inventory/summary`
  - `GET /stats`

## Старт
```bash
cp .env.example .env
docker compose up -d --build
```

Проверка:
- http://localhost:8000/health
- Swagger: http://localhost:8000/docs

## Импорт CSV (вариант 1 — загрузить файл)
Ожидаемый формат CSV:
- `item_name`
- `location`
- `qty_available`

Пример:
```bash
curl -X POST "http://localhost:8000/import/inventory"   -F "file=@data/processed/inventory_normalized_aggregated.csv"
```

## Импорт CSV (вариант 2 — файл уже лежит в ./data)
```bash
curl -X POST "http://localhost:8000/import/inventory-from-path?rel_path=processed/inventory_normalized_aggregated.csv"
```

## Посмотреть что загрузилось
```bash
curl "http://localhost:8000/stats"
curl "http://localhost:8000/inventory?limit=20"
curl "http://localhost:8000/inventory?item=компьютер&limit=20"
curl "http://localhost:8000/inventory?location=201В&limit=50"
```
