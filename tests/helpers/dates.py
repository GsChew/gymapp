from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    return datetime.now(UTC)


def future_datetime(*, days: int = 7, hours: int = 0) -> datetime:
    return utc_now() + timedelta(days=days, hours=hours)


def past_datetime(*, days: int = 1) -> datetime:
    return utc_now() - timedelta(days=days)


def to_api_datetime(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
