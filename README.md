# Gym Planner / Stride

Gym Planner / Stride — бэкенд и простой web-интерфейс для планирования тренировок.
Приложение помогает пользователю вести тренировки, собирать планы из упражнений,
создавать цели, работать с шаблонами, смотреть прогресс и получать напоминания.

## Возможности

- регистрация, логин, refresh-токены и текущий профиль пользователя;
- роли `user`, `trainer`, `admin` и проверка доступа к административным действиям;
- CRUD тренировок, фильтрация по статусу, стартовый план и отметка тренировки выполненной;
- конструктор тренировки через связи `workout-exercises`;
- каталог упражнений с ограничением создания/изменения для тренера или администратора;
- цели пользователя;
- шаблоны тренировок и создание тренировки из шаблона;
- прогресс: сводка, недельный объем, рекорды и история по упражнению;
- уведомления о тренировках через Celery;
- rate limit через Redis;
- централизованное логирование через Loguru;
- тестовый набор: unit, smoke, contract, API, security, integration и UI;
- одинаковые browser E2E-сценарии на Selenium и Playwright с Page Object.

## Архитектура

Бэкенд построен на FastAPI и разделен по слоям:

```text
router -> service -> repository -> database
```

- `router` принимает HTTP-запрос, валидирует вход через Pydantic-схемы и вызывает сервис;
- `service` содержит бизнес-логику, проверки доступа, сценарии и прикладное логирование;
- `repository` отвечает за запросы к базе данных;
- `models` описывает SQLAlchemy-модели;
- `schemas` описывает Pydantic-контракты API.

Основные папки:

- `src/auth` — аутентификация, JWT, зависимости и роли;
- `src/workouts` — сценарии тренировок;
- `src/workout_exercises` — упражнения внутри тренировок;
- `src/exercises` — справочник упражнений;
- `src/goals` — цели пользователя;
- `src/templates` — шаблоны тренировок;
- `src/progress` — расчет прогресса;
- `src/notifications` — уведомления;
- `src/rate_limit` — зависимости rate limit;
- `src/repository` — слой доступа к данным;
- `src/models` — ORM-модели;
- `src/schemas` — API-схемы;
- `tests` — автоматические тесты;
- `docs` — документация проекта.

Подробнее: [docs/ARCHITECTURE_RU.md](docs/ARCHITECTURE_RU.md).

## Быстрый запуск

Создай `.env` в корне проекта. Минимальный набор переменных:

```env
DATABASE_URL=postgresql+asyncpg://gymuser:gympassword@localhost:5433/gymapp
ALEMBIC_DATABASE_URL=postgresql+psycopg://gymuser:gympassword@localhost:5433/gymapp
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_JSON=false
```

Поднять инфраструктуру и приложение:

```bash
docker compose up -d --build
```

Локальный запуск без контейнера приложения:

```bash
source .venv/bin/activate
alembic upgrade head
uvicorn main:app --reload
```

После запуска:

- frontend: `http://127.0.0.1:8000/`;
- health check: `http://127.0.0.1:8000/health`;
- OpenAPI: `http://127.0.0.1:8000/docs`.

## Логирование

Логирование настроено в `src/logging_config.py`.

Используется Loguru:

- консольный лог;
- файл `logs/app.log`;
- отдельный файл ошибок `logs/error.log`;
- `request_id` для связывания логов одного HTTP-запроса;
- middleware с логами входящих запросов, статусов и времени выполнения.

Управляющие переменные:

- `LOG_LEVEL` — уровень логов, например `INFO` или `DEBUG`;
- `LOG_DIR` — директория логов;
- `LOG_JSON` — JSON-формат для контейнеров и централизованного сбора логов.

## Тесты

Установка и быстрый набор:

```bash
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
python -m playwright install chromium
pytest -m "unit or smoke or contract" -q
```

API и integration tests используют отдельные PostgreSQL/Redis/RabbitMQ:

```bash
docker compose -f docker-compose.test.yml up -d \
  test-db test-redis test-rabbitmq
pytest -q
```

UI-наборы запускаются отдельно:

```bash
pytest -m "ui and selenium"
pytest -m "ui and playwright"
```

Coverage и Allure:

```bash
pytest --cov=src --cov=main --cov-report=html \
  --alluredir=allure-results
```

Полное описание архитектуры, переменных, markers, Docker, CI и расширения
framework: [TESTING.md](TESTING.md).

## Документация

- [docs/API_RU.md](docs/API_RU.md) — обзор API;
- [docs/ARCHITECTURE_RU.md](docs/ARCHITECTURE_RU.md) — архитектура и правила разработки;
- [docs/QA_TESTING_GUIDE.txt](docs/QA_TESTING_GUIDE.txt) — QA-гайд;
- [docs/QA_TEST_IMPLEMENTATION_REPORT.txt](docs/QA_TEST_IMPLEMENTATION_REPORT.txt) — отчет о реализованном тестовом покрытии.
