# Архитектура проекта

Документ фиксирует, как в проекте принято раскладывать код, где должна жить
логика и как поддерживать структуру без разрастания router-файлов.

## Главный принцип

В проекте используется разделение:

```text
router -> service -> repository -> database
```

Это правило важно для всех новых фич.

- `router` знает про HTTP: route, Depends, Query, status code и response model;
- `service` знает про бизнес-сценарий: права, проверки, ветвления, логирование, orchestration;
- `repository` знает про SQLAlchemy и запросы к базе;
- `schemas` описывает входные и выходные контракты API;
- `models` описывает таблицы и связи.

Если в router появляется сложная логика, ее нужно переносить в service.
Если в service появляется SQL-запрос, его нужно переносить в repository.

## Структура модулей

Типовая фича выглядит так:

```text
src/<feature>/
  router.py
  service.py

src/repository/<feature>.py
src/models/<feature>.py
src/schemas/<feature>.py
```

Для маленькой фичи допустимо не создавать лишние файлы, но публичный HTTP-flow
все равно должен оставаться тонким в router.

## Текущие домены

- `auth` — регистрация, логин, refresh, текущий пользователь;
- `users` — административные операции над пользователями;
- `workouts` — тренировки и жизненный цикл тренировки;
- `workout_exercises` — упражнения, привязанные к тренировке;
- `exercises` — справочник упражнений;
- `goals` — пользовательские цели;
- `templates` — шаблоны тренировок;
- `progress` — аналитика и история прогресса;
- `notifications` — уведомления и фоновые напоминания;
- `rate_limit` — ограничение частоты запросов.

## Логирование

Логирование подключается через `setup_app_logging(app)` в `main.py`.
Настройка находится в `src/logging_config.py`.

Что логировать:

- создание, изменение и удаление сущностей;
- отказ доступа и нарушение ownership;
- значимые бизнес-события: завершение тренировки, создание starter plan, refresh токена;
- фоновые задачи;
- ошибки внешней инфраструктуры: БД, Redis, RabbitMQ;
- подозрительные security-события без записи паролей и токенов.

Что не логировать:

- пароль;
- access token и refresh token;
- полные Authorization-заголовки;
- персональные данные без необходимости.

## Комментарии к функциям

В проекте уместны короткие docstring-комментарии у публичных service/repository
функций, зависимостей и сложной бизнес-логики. Комментарий должен объяснять
назначение и важные ограничения, а не пересказывать код построчно.

Хороший пример:

```python
async def create_workout_from_template(...):
    """Create a user workout and exercise links from an owned template."""
```

Плохой пример:

```python
async def get_user(...):
    """Gets user."""
```

## Миграции

Изменение моделей должно сопровождаться Alembic-миграцией:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Миграцию нужно читать перед коммитом: autogenerate может создать лишние или
опасные операции.

## Тестирование изменений

Минимальный набор для backend-изменений:

```bash
pytest tests/unit tests/smoke tests/contract -q
```

Если менялись API, repository или модели:

```bash
REQUIRE_TEST_INFRA=1 pytest tests/api tests/security -q
```

Если менялся frontend:

```bash
RUN_E2E=1 BASE_URL=http://127.0.0.1:8000 pytest tests/e2e/test_browser_playwright.py -q
```

Если менялся JavaScript:

```bash
node --check static/app.js
```

## Правила для новых фич

1. Начинай со схемы данных и контракта API.
2. Добавляй router только как HTTP-обвязку.
3. Бизнес-логику держи в service.
4. SQL-запросы держи в repository.
5. Добавляй логи в service на значимых событиях.
6. Покрывай позитивный, негативный и хотя бы один граничный сценарий.
7. Обновляй документацию, если меняется публичное поведение.
