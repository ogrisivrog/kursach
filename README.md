# MTO (minimal start)

## Что есть сейчас
- PostgreSQL (docker)
- FastAPI backend (docker)
- **Фронтенд** (React + Vite) — дашборд, инвентарь, требования, покрытие, отчёты, AI-записка
- Таблицы: `items`, `locations`, `inventory`, требования, ПО
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
- Бэкенд: http://localhost:8000/health
- Swagger: http://localhost:8000/docs
- **Фронтенд:** http://localhost:5173

Локальная разработка фронтенда (без Docker):
```bash
cd frontend && npm install && npm run dev
```
Фронтенд будет доступен на http://localhost:5173 и обращается к API на http://localhost:8000 (прокси в Vite).

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
