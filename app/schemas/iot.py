from pydantic import BaseModel
from datetime import datetime


class EspHealthPayload(BaseModel):

    device_code: str
    seq: int | None = None

    heart_rate: int | None = None
    spo2: int | None = None

    temperature: float | None = None
    humidity: float | None = None
    gas_level: float | None = None

    blood_pressure: str | None = None

    sent_at: datetime | None = None
    measured_at: datetime | None = None

    is_offline: bool = False