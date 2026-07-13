from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.schemas.data_quality import DataQualitySummaryRead
from app.services.data_quality import DataQualitySummaryService


router = APIRouter(
    tags=["admin-data-quality"],
    dependencies=[Depends(require_admin)],
)


@router.get("/data-quality-summary", response_model=DataQualitySummaryRead)
def get_data_quality_summary(
    year: str | None = Query(default=None),
    source: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return DataQualitySummaryService().build(db, year=year, source=source)
