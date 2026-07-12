from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PaginationMeta, PaginatedResponse
from app.schemas.players import PlayerCreate, PlayerRead
from app.schemas.results import PlayerStatisticsResponseRead, RaceHistoryRead
from app.services.results import ResultService
from app.services.players import PlayerService

router = APIRouter(prefix="/players", tags=["players"])
service = PlayerService()
result_service = ResultService()


@router.get("", response_model=PaginatedResponse[PlayerRead])
def list_players(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = service.list_players(db, page=page, page_size=page_size)
    return {
        "items": items,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total),
    }


@router.get("/{player_id}", response_model=PlayerRead)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = service.get_player(db, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@router.post("", response_model=PlayerRead, status_code=status.HTTP_201_CREATED)
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    try:
        return service.create_player(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{player_id}/statistics", response_model=PlayerStatisticsResponseRead)
def get_player_statistics(
    player_id: int,
    track_id: int | None = Query(default=None, ge=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    last_n: int | None = Query(default=None, ge=1, le=1000),
    grade: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        payload = result_service.get_player_statistics(
            db,
            player_id,
            track_id=track_id,
            date_from=date_from,
            date_to=date_to,
            last_n=last_n,
            grade=grade,
        )
        return payload
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{player_id}/race-history", response_model=RaceHistoryRead)
def get_player_race_history(player_id: int, db: Session = Depends(get_db)):
    try:
        player, results = result_service.get_player_race_history(db, player_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {
        "player_id": player.id,
        "player_name": player.name,
        "player_number": player.player_number,
        "grade": player.grade,
        "region": player.region,
        "history": [
            {
                "race_id": result.race.id,
                "race_date": result.race.race_date,
                "track_name": result.race.track_name,
                "race_number": result.race.race_number,
                "scheduled_start_time": result.race.scheduled_start_time,
                "result_status": result.result_status,
                "finish_position": result.finish_position,
                "finish_time": result.finish_time,
                "points": result.points,
            }
            for result in results
        ],
    }
