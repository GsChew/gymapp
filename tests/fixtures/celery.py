from __future__ import annotations

from collections.abc import Iterator

import pytest

from src.celery_app import celery_app


@pytest.fixture
def celery_eager() -> Iterator:
    previous = {
        "task_always_eager": celery_app.conf.task_always_eager,
        "task_eager_propagates": celery_app.conf.task_eager_propagates,
        "task_store_eager_result": celery_app.conf.task_store_eager_result,
    }
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
    )
    yield celery_app
    celery_app.conf.update(**previous)
