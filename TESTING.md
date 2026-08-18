# Testing Gym Planner

## Назначение

Тестовый фреймворк проверяет фактически реализованные FastAPI-контракты,
бизнес-сервисы и интеграции Gym Planner. Источником истины остаётся код
приложения: тесты не вводят endpoints, поля или ограничения, отсутствующие в
роутерах, Pydantic-схемах, SQLAlchemy-моделях и сервисах.

Основной стек:

- `pytest` и `pytest-asyncio`;
- `httpx.AsyncClient` с `ASGITransport`;
- PostgreSQL 16 через `asyncpg`;
- Redis 7 для реального sliding-window rate limit;
- Celery в eager-режиме и с реальной PostgreSQL-сессией задачи;
- Selenium WebDriver и Playwright для одинаковых browser E2E-сценариев;
- `pytest-cov` с branch coverage;
- Allure;
- Ruff для test-кода.

SQLite намеренно не используется.

## Архитектура

```text
tests/
├── api/
│   ├── auth/              # регистрация, login, refresh, JWT
│   ├── users/             # роли и административные операции
│   ├── workouts/          # CRUD, completion, workout-exercises
│   ├── exercises/         # каталог и RBAC
│   ├── notifications/     # личный inbox
│   ├── planning/          # goals, templates, progress
│   └── security/          # privilege boundaries и injection strings
├── clients/
│   ├── base_client.py     # HTTP transport, timeout, Bearer, safe logging
│   └── api.py             # resource clients без assertions
├── factories/             # валидные уникальные request payloads
├── fixtures/
│   ├── config.py          # test environment
│   ├── database.py        # test DB, schema и очистка
│   ├── app.py             # FastAPI override и AsyncClient
│   ├── users.py           # user/trainer/admin и токены
│   ├── resources.py       # ORM resource builders
│   └── celery.py          # eager configuration
├── helpers/               # dates, JWT, assertions, polling, redaction
├── integration/
│   ├── database/          # constraints, FK, cascade, Alembic
│   ├── celery/            # registration, eager и DB behavior
│   └── redis/             # реальный Redis
├── ui/
│   ├── selenium/
│   │   ├── pages/         # Selenium Page Object
│   │   └── test_ui_journey.py
│   └── playwright/
│       ├── pages/         # Playwright Page Object
│       └── test_ui_journey.py
├── contract/              # OpenAPI
├── smoke/                 # startup, health, static, critical auth
└── unit/                  # schemas, security, services, error branches
```

Разделение ответственности:

- API client только формирует и отправляет запрос, затем возвращает
  `httpx.Response`;
- fixture создаёт окружение или данные;
- factory строит payload и разрешает точечные overrides;
- helper решает техническую переиспользуемую задачу;
- конкретные бизнес-assertions находятся в тесте.

При падении API-теста hook в `tests/conftest.py` добавляет в Allure историю
запросов и ответов. `Authorization`, пароли, access/refresh tokens и secret
поля редактируются.

## Установка

Рекомендуется Python 3.13, как в основном Dockerfile.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
python -m playwright install chromium
```

Selenium использует установленный Chrome/Chromium и совместимый ChromeDriver.
В Docker они устанавливаются из Debian packages. При нестандартной локальной
установке задайте `UI_BROWSER_BINARY` и `UI_DRIVER_BINARY`.

## Переменные окружения

Создайте локальный файл:

```bash
cp .env.test.example .env.test
```

Загрузите его в текущую shell-сессию:

```bash
set -a
source .env.test
set +a
```

Ключевые переменные:

- `TEST_DATABASE_URL` — async PostgreSQL URL;
- `TEST_ALEMBIC_DATABASE_URL` — sync URL для Alembic;
- `TEST_REDIS_URL` — отдельный Redis;
- `TEST_API_TIMEOUT` — timeout клиента;
- `REQUIRE_TEST_INFRA=1` — падать, а не skip, если инфраструктура недоступна.
- `UI_HEADLESS=1` — запускать браузеры без окна;
- `UI_BROWSER_BINARY` — необязательный путь к Chromium;
- `UI_DRIVER_BINARY` — необязательный путь к ChromeDriver для Selenium.

Перед destructive schema setup framework проверяет, что имя БД заканчивается
на `_test`, и отказывается работать с `gymapp`, `postgres`, `template0` и
`template1`.

Значения в `.env.test.example` — disposable local credentials. Не используйте
production secrets и production database.

## Локальный запуск

Быстрые наборы без инфраструктуры:

```bash
pytest -m smoke
pytest -m unit
pytest -m contract
```

Полный набор после запуска test infrastructure:

```bash
pytest
```

Основные выборки:

```bash
pytest -m api
pytest -m auth
pytest -m security
pytest -m integration
pytest -m database
pytest -m celery
pytest -m redis
pytest -m "ui and selenium"
pytest -m "ui and playwright"
pytest -m ui
pytest -m positive
pytest -m negative
```

Конкретный модуль или тест:

```bash
pytest tests/api/workouts/test_workouts_crud_api.py
pytest tests/api/auth/test_auth_api.py::test_register_login_refresh_and_me
```

`pytest.ini` включает strict markers, strict config, `asyncio_mode=strict` и
единый session event loop. Параллельный `xdist` намеренно не включён: API и
integration tests используют одну test DB и выполняют `TRUNCATE ... CASCADE`
между тестами.

## UI и Page Object

Selenium и Playwright выполняют одинаковые сценарии:

1. переключение формы входа и регистрации;
2. безопасная ошибка при входе неизвестного пользователя;
3. регистрация, создание тренировки, проверка плана и logout.
4. проверка, что authenticated view скрывает форму входа (`UI-001`, `xfail`).

Каждый стек имеет собственные `BasePage`, `AuthPage` и `DashboardPage`.
Селекторы, ожидания и browser-действия находятся в Page Object; assertions и
бизнес-последовательность остаются в тестах. Поэтому тесты читаются одинаково,
но не скрывают различия API Selenium и Playwright.

Session fixture запускает реальный Uvicorn на свободном loopback-порту.
Браузеры взаимодействуют с настоящим FastAPI API, PostgreSQL и Redis. Перед и
после каждого UI-теста очищаются application tables и выделенная Redis DB.
HTTP mocking не применяется.

UI-тесты работают headless по умолчанию. Чтобы увидеть браузер:

```bash
UI_HEADLESS=0 pytest -m "ui and playwright"
```

При падении текущая страница автоматически прикладывается к Allure в PNG.
Внешний CDN иконок блокируется, потому что он не является предметом теста и не
должен влиять на стабильность локального E2E.

## Docker

Test compose имеет отдельный project name `gymapp-tests`, отдельные порты и
tmpfs PostgreSQL. Он не использует основной контейнер `gymapp_db`.

Поднять только инфраструктуру для запуска pytest из `.venv`:

```bash
docker compose -f docker-compose.test.yml up -d \
  test-db test-redis test-rabbitmq
```

Проверить состояние:

```bash
docker compose -f docker-compose.test.yml ps
```

Запустить миграции и весь набор внутри Docker:

```bash
docker compose -f docker-compose.test.yml up \
  --build --abort-on-container-exit --exit-code-from tests tests
```

Удалить только тестовый stack:

```bash
docker compose -f docker-compose.test.yml down
```

## Изоляция PostgreSQL

Сессия тестов один раз создаёт metadata в безопасной test DB. Перед и после
каждого теста все application tables очищаются командой:

```sql
TRUNCATE TABLE ... RESTART IDENTITY CASCADE
```

Такой подход выбран потому, что repositories приложения делают `commit`
внутри CRUD-методов. Внешний rollback не отменил бы уже committed данные.

Каждый тест получает новую `AsyncSession`; пользователи и ресурсы уникальны.
Тесты не зависят от порядка и не используют заранее изменяемые общие записи.
Миграционная цепочка отдельно проверяется через Alembic и в CI выполняется
`alembic upgrade head`.

## Celery

Есть два уровня:

1. eager-проверки подтверждают регистрацию задачи, её сигнатуру и sync wrapper;
2. integration-проверки вызывают реальную async-логику задачи с отдельной
   SQLAlchemy session factory и проверяют PostgreSQL.

Проверяются due reminder, статусы planned/done/missed, будущий reminder,
rollback dependency error и повторный вызов без duplicate notification.
Реальный RabbitMQ поднимается в test stack и CI, но broker round-trip не
дублирует уже проверенную прикладную логику задачи.

## Coverage

Корректная команда измеряет только application code:

```bash
pytest --cov=src --cov=main \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-report=html
```

Источники покрытия указываются явно: голый `pytest --cov` считает также код
самого тестового фреймворка и поэтому не используется для итоговой метрики.
Порог — 80%. Миграции, tests и сгенерированные артефакты не входят в процент.
HTML-отчёт создаётся в `htmlcov/`, XML — `coverage.xml`.

## Allure

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

Feature/story/severity используются на критичных бизнес-сценариях. Steps
отмечают только значимые действия. HTTP attachments появляются при падении и
не содержат secrets.

## Добавление нового API client

1. Добавьте resource client в `tests/clients/api.py`.
2. Принимайте `BaseClient` через конструктор.
3. Создавайте бизнес-методы, возвращающие `Response`.
4. Не добавляйте assertions и автоматические retry.
5. Зарегистрируйте client в `ApiClients.build`.

Пример:

```python
class ReportsClient:
    def __init__(self, client: BaseClient) -> None:
        self.client = client

    async def get_report(self, report_id: int):
        return await self.client.get(f"/reports/{report_id}")
```

## Добавление fixture

Размещайте fixture в модуле по ответственности. Если создаётся ORM-ресурс,
используйте function scope, выполняйте явный `commit/refresh` и возвращайте
модель. Если добавляется новый fixture-модуль, зарегистрируйте его в
`pytest_plugins` внутри `tests/conftest.py`.

Fixture не должна скрывать assertions бизнес-сценария. Допустимы технические
precondition assertions, когда без них тест не может продолжаться.

## Добавление factory

Factory должна:

- создавать валидный объект по умолчанию;
- генерировать уникальные поля;
- принимать overrides;
- не обращаться к сети или БД;
- не хранить постоянные пароли и tokens.

Пароли пользователей генерируются в runtime через `secrets`.

## Добавление теста

1. Определите один логический сценарий.
2. Используйте Arrange–Act–Assert.
3. Выберите существующий marker.
4. Возьмите данные из factory и окружение из fixture.
5. Отправьте запрос через resource client.
6. Проверьте status, body и, если важно, наблюдаемое состояние PostgreSQL.
7. Для настоящего дефекта используйте `xfail(strict=True)` с defect id и
   причиной; не меняйте ожидание на текущее неправильное поведение.

Для нового UI-раздела сначала добавьте действия и селекторы в соответствующий
Page Object Selenium и Playwright, затем добавьте один и тот же бизнес-сценарий
в оба `test_ui_journey.py`. Не размещайте WebDriver/Locator-вызовы напрямую в
тесте.

## Диагностика

### Все API-тесты skipped

PostgreSQL недоступен. Поднимите test stack и проверьте
`TEST_DATABASE_URL`. Для CI-подобного поведения задайте
`REQUIRE_TEST_INFRA=1`.

### Framework отказывается очищать БД

Имя БД не заканчивается `_test` или относится к protected names. Создайте
отдельную test DB; не отключайте safety check.

### `Operation not permitted` при подключении к localhost

Это ограничение sandbox/IDE. Разрешите процессу Python локальные сетевые
подключения либо запускайте suite внутри `docker-compose.test.yml`.

### Redis-тест skipped

Проверьте health сервиса `test-redis` и `TEST_REDIS_URL`.

### Selenium не находит ChromeDriver

Проверьте версии Chrome/Chromium и ChromeDriver. При необходимости явно
задайте `UI_BROWSER_BINARY` и `UI_DRIVER_BINARY`. В Docker эти значения уже
настроены.

### Playwright сообщает `Executable doesn't exist`

Установите browser bundle:

```bash
python -m playwright install chromium
```

### `MissingGreenlet`

Не читайте expired ORM attributes синхронно после rollback. Сохраните scalar id
до rollback или выполните явный `await session.refresh(model)`.

### Allure не показывает HTTP

Attachments добавляются только при падении call phase. Убедитесь, что тест
использует client из `api_clients_factory`.

### Coverage неожиданно включает tests

Используйте `--cov=src --cov=main`; CI и Docker уже настроены именно так.
