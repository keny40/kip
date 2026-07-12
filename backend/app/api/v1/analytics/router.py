from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import RaceSummaryRead, TrackPlayerStatRead, TrackSummaryRead
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
service = AnalyticsService()


@router.get("/tracks/{track_id}/summary", response_model=TrackSummaryRead)
def get_track_summary(track_id: int, db: Session = Depends(get_db)):
    try:
        return service.track_summary(db, track_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tracks/{track_id}/players", response_model=list[TrackPlayerStatRead])
def get_track_players(track_id: int, db: Session = Depends(get_db)):
    try:
        return service.track_players(db, track_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/races/summary", response_model=RaceSummaryRead)
def get_races_summary(db: Session = Depends(get_db)):
    return service.races_summary(db)
