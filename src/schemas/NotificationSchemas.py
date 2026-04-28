from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SNotification(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SNotificationCreate(BaseModel):
    user_id: int
    workout_id: int | None = None
    title: str
    message: str

class SNotificationUpdate(BaseModel):
    is_read: bool