from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import PaginationMeta, PaginatedResponse
from app.schemas.results import (
    RaceResultsRead,
    ResultCreate,
    ResultDetailRead,
    ResultListItemRead,
    ResultRead,
    ResultUpdate,
)
from app.services.results import ResultService

router = APIRouter(tags=["results"])
service = ResultService()


def _race_payload(race, results) -> RaceResultsRead:
    return RaceResultsRead(
        race_id=race.id,
        race_date=race.race_date,
        track_name=race.track_name,
        race_number=race.race_number,
        scheduled_start_time=race.scheduled_start_time,
        status=race.status,
        results=results,
    )


def _result_list_item(result) -> ResultListItemRead:
    return ResultListItemRead(
        id=result.id,
        race_id=result.race_id,
        player_id=result.player_id,
        race_date=result.race.race_date,
        track_name=result.race.track_name,
        result_status=result.result_status,
        finish_position=result.finish_position,
        points=result.points,
    )


@router.get("/results", response_model=PaginatedResponse[ResultListItemRead])
def list_results(
    race_id: int | None = Query(default=None),
    player_id: int | None = Query(default=None),
    race_date: date | None = Query(default=None),
    track_name: str | None = Query(default=None),
    result_status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = service.list_results(
        db,
        race_id=race_id,
        player_id=player_id,
        race_date=race_date,
        track_name=track_name,
        result_status=result_status,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [_result_list_item(item) for item in items],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total),
    }


@router.get("/results/{result_id}", response_model=ResultDetailRead)
def get_result(result_id: int, db: Session = Depends(get_db)):
    result = service.get_result(db, result_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    return result


@router.post("/results", response_model=ResultDetailRead, status_code=status.HTTP_201_CREATED)
def create_result(payload: ResultCreate, db: Session = Depends(get_db)):
    try:
        return service.create_result(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/races/{race_id}/results", response_model=RaceResultsRead)
def get_race_results(race_id: int, db: Session = Depends(get_db)):
    try:
        race, results = service.race_results_payload(db, race_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _race_payload(race, results)


@router.put("/results/{result_id}", response_model=ResultDetailRead)
def update_result(result_id: int, payload: ResultUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_result(db, result_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: int, db: Session = Depends(get_db)):
    try:
        service.delete_result(db, result_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
