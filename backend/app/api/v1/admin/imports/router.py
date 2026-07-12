from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.core.config import settings
from app.db.session import get_db
from app.schemas.imports import ImportResponseRead, ImportType
from app.services.imports.upload import CSVUploadService

router = APIRouter(
    prefix="/imports",
    tags=["admin-imports"],
    dependencies=[Depends(require_admin)],
)

service = CSVUploadService()

SUPPORTED_IMPORT_TYPES = {item.value for item in ImportType}


@router.post(
    "/{import_type}",
    response_model=ImportResponseRead,
    summary="Admin CSV import",
    description=(
        "관리자 전용 CSV 업로드 엔드포인트입니다. "
        "지원 import_type: tracks, players, races, entries, results. "
        "권장 순서: tracks -> players -> races -> entries -> results. "
        "dry_run=true이면 DB를 변경하지 않습니다. "
        f"최대 파일 크기: {settings.csv_import_max_bytes} bytes."
    ),
)
def import_csv(
    import_type: str,
    file: UploadFile | None = File(default=None, description="CSV file to import"),
    dry_run: bool = Query(default=False, description="Validate without changing the database"),
    db: Session = Depends(get_db),
) -> ImportResponseRead:
    if import_type not in SUPPORTED_IMPORT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported import_type")
    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is required")
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file must have a filename")

    try:
        return service.import_upload(db, import_type=ImportType(import_type), upload_file=file, dry_run=dry_run)
    except OverflowError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "admin-imports", "status": "ready"}
