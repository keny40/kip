from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.race_history_analytics import RaceHistoryAnalyticsService


router = APIRouter(prefix="/analytics/history", tags=["history-analytics"])


@router.get("/players")
def get_history_players(
    year: str | None = Query(default=None),
    meet_name: str | None = Query(default=None),
    period_number: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    minimum_starts: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return RaceHistoryAnalyticsService().players(
        db,
        year=year,
        meet_name=meet_name,
        period_number=period_number,
        grade=grade,
        minimum_starts=minimum_starts,
    )


@router.get("/players/{name}")
def get_history_player(name: str, db: Session = Depends(get_db)):
    return [item for item in RaceHistoryAnalyticsService().players(db) if item["player_name"] == name]


@router.get("/tracks")
def get_history_tracks(
    year: str | None = Query(default=None),
    meet_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return RaceHistoryAnalyticsService().tracks(db, year=year, meet_name=meet_name)


@router.get("/summary")
def get_history_summary(year: str | None = Query(default=None), db: Session = Depends(get_db)):
    return RaceHistoryAnalyticsService().summary(db, year=year)
