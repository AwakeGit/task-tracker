# Трекер задач

REST-сервис для учёта задач: CRUD, фильтрация, смена статусов, аналитика с графиками, JWT-аутентификация.

## Стек

FastAPI, PostgreSQL, SQLAlchemy 2, Alembic, pandas, matplotlib, pytest.

## Запуск

```bash
docker compose up -d
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

## Переменные окружения

Настройки подключения и безопасности переопределяются через env-переменные
(читаются `pydantic-settings`):

- `DATABASE_URL` — строка подключения к PostgreSQL (по умолчанию совпадает с docker-compose).
- `SECRET_KEY` — секрет для подписи JWT. Значение по умолчанию только для локальной разработки,
  в любом другом окружении задайте свой ключ.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — время жизни токена (по умолчанию 60).

## Примеры запросов

```bash
# регистрация
curl -X POST localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "pavel@example.com", "name": "Pavel", "password": "secret123"}'

# логин (OAuth2 password form)
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d "username=pavel@example.com&password=secret123" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# создание задачи
curl -X POST localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title": "Сделать ДЗ", "theme": "учёба"}'

# список с фильтром
curl "localhost:8000/tasks?status=new&theme=учёба" -H "Authorization: Bearer $TOKEN"

# смена статуса
curl -X PATCH localhost:8000/tasks/1/status \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# аналитика
curl localhost:8000/analytics/summary -H "Authorization: Bearer $TOKEN"
curl localhost:8000/analytics/status-chart -H "Authorization: Bearer $TOKEN" --output chart.png
```

## Тесты

```bash
./.venv/bin/python -m pytest tests/ -v
```

Тесты используют SQLite in-memory (переопределение зависимости `get_db`), миграции не требуются.

## Модель данных

ERD описан в `ERD.md`. Две сущности: `users` и `tasks` (связи: владелец задачи и исполнитель — обе ссылаются на `users`).

## Безопасность

- Пароли хэшируются bcrypt.
- Аутентификация — JWT (HS256), токен передаётся в заголовке `Authorization: Bearer`.
- Все запросы к БД выполняются через SQLAlchemy ORM с параметризованными выражениями, что исключает SQL-инъекции (есть тест `test_filter_is_parameterized`).
- Редактировать и удалять задачу может только её владелец.
