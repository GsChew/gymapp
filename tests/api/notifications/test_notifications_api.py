from datetime import timedelta

import allure
import pytest

from src.models.notification import NotificationModel
from tests.helpers.assertions import assert_error
from tests.helpers.dates import utc_now


pytestmark = [pytest.mark.api]


@allure.feature("Notifications")
@allure.story("Personal inbox")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_user_lists_filters_reads_and_deletes_own_notifications(
    user_account,
    make_notification,
    db_session,
) -> None:
    unread = await make_notification(
        user_id=user_account.user.id,
        title="Unread",
        created_at=utc_now(),
    )
    read = await make_notification(
        user_id=user_account.user.id,
        title="Read",
        is_read=True,
        created_at=utc_now() - timedelta(minutes=1),
    )

    all_items = await user_account.clients.notifications.list_notifications()
    unread_items = await user_account.clients.notifications.list_notifications(
        is_read=False
    )
    count_before = await user_account.clients.notifications.unread_count()

    assert all_items.status_code == 200
    assert [item["id"] for item in all_items.json()] == [unread.id, read.id]
    assert [item["id"] for item in unread_items.json()] == [unread.id]
    assert count_before.json() == {"unread_count": 1}

    marked = await user_account.clients.notifications.mark_read(unread.id)
    count_after = await user_account.clients.notifications.unread_count()
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
    assert count_after.json() == {"unread_count": 0}

    deleted = await user_account.clients.notifications.delete_notification(read.id)
    assert deleted.status_code == 200
    assert await db_session.get(NotificationModel, read.id) is None


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_notification_isolation_hides_foreign_resource(
    user_account,
    make_user,
    make_notification,
) -> None:
    stranger = await make_user()
    notification = await make_notification(user_id=user_account.user.id)

    detail = await stranger.clients.notifications.get_notification(notification.id)
    read = await stranger.clients.notifications.mark_read(notification.id)
    delete = await stranger.clients.notifications.delete_notification(
        notification.id
    )
    listing = await stranger.clients.notifications.list_notifications()

    for response in (detail, read, delete):
        assert_error(response, 404)
    assert listing.json() == []
    owner_detail = await user_account.clients.notifications.get_notification(
        notification.id
    )
    assert owner_detail.status_code == 200
    assert owner_detail.json()["is_read"] is False


@pytest.mark.negative
@pytest.mark.asyncio
async def test_notification_pagination_validation_and_repeat_delete(
    user_account,
    make_notification,
) -> None:
    first = await make_notification(
        user_id=user_account.user.id,
        created_at=utc_now() - timedelta(minutes=1),
    )
    second = await make_notification(
        user_id=user_account.user.id,
        created_at=utc_now(),
    )

    page_one = await user_account.clients.notifications.list_notifications(
        limit=1,
        offset=0,
    )
    page_two = await user_account.clients.notifications.list_notifications(
        limit=1,
        offset=1,
    )
    invalid_limit = await user_account.clients.notifications.list_notifications(
        limit=0
    )
    missing = await user_account.clients.notifications.get_notification(999_999)
    deleted = await user_account.clients.notifications.delete_notification(first.id)
    repeated = await user_account.clients.notifications.delete_notification(first.id)

    assert page_one.json()[0]["id"] == second.id
    assert page_two.json()[0]["id"] == first.id
    assert_error(invalid_limit, 422)
    assert_error(missing, 404)
    assert deleted.status_code == 200
    assert_error(repeated, 404)
