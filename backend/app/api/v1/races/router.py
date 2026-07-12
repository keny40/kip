from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PaginationMeta, PaginatedResponse
from app.schemas.races import RaceCreate, RaceDetailRead, RaceRead
from app.services.races import RaceService

router = APIRouter(prefix="/races", tags=["races"])
service = RaceService()


@router.get("", response_model=PaginatedResponse[RaceRead])
def list_races(
    race_date: date | None = Query(default=None),
    track_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = service.list_races(
        db,
        race_date=race_date,
        track_name=track_name,
        status=status,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total),
    }


@router.get("/{race_id}", response_model=RaceDetailRead)
def get_race(race_id: int, db: Session = Depends(get_db)):
    race = service.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")
    return race


@router.post("", response_model=RaceRead, status_code=status.HTTP_201_CREATED)
def create_race(payload: RaceCreate, db: Session = Depends(get_db)):
    try:
        return service.create_race(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
