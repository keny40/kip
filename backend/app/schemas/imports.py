from enum import Enum

from pydantic import Field

from app.schemas.common import ORMModel


class ImportType(str, Enum):
    tracks = "tracks"
    players = "players"
    races = "races"
    entries = "entries"
    results = "results"


class ImportErrorRead(ORMModel):
    row_number: int
    error_code: str
    error_message: str


class ImportResponseRead(ORMModel):
    import_type: ImportType
    filename: str
    dry_run: bool
    total: int
    created: int
    updated: int = Field(default=0)
    skipped: int
    failed: int
    errors: list[ImportErrorRead]
