from uuid import uuid4


def unique_suffix() -> str:
    return uuid4().hex


def unique_username(prefix: str = "qa") -> str:
    return f"{prefix}_{unique_suffix()[:16]}"


def unique_email(prefix: str = "qa") -> str:
    return f"{prefix}_{unique_suffix()[:16]}@example.com"
