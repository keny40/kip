from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.services.race_history_analytics import RaceHistoryAnalyticsService


router = APIRouter(tags=["admin-race-history-quality"], dependencies=[Depends(require_admin)])


@router.get("/race-history-data-quality")
def get_race_history_data_quality(db: Session = Depends(get_db)):
    return RaceHistoryAnalyticsService().quality(db)
