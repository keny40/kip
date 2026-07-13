from datetime import datetime

from app.schemas.common import ORMModel


class ExternalPlayerRead(ORMModel):
    id: int
    source: str
    external_id: str
    name: str
    period_number: str | None
    grade: str
    region: str
    status: str
    detail_url: str | None
    source_updated_at: datetime | None
    collected_at: datetime
    created_at: datetime
    updated_at: datetime
