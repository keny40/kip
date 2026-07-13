from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.repositories.external_player_statistics import ExternalPlayerStatisticRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.external_player_statistics import (
    ExternalPlayerStatisticRead,
    PlayerMatchCandidateRead,
)
from app.services.player_match_candidates import PlayerMatchCandidateService


router = APIRouter(
    tags=["admin-external-player-statistics"],
    dependencies=[Depends(require_admin)],
)
repository = ExternalPlayerStatisticRepository()


@router.get(
    "/external-player-statistics",
    response_model=PaginatedResponse[ExternalPlayerStatisticRead],
)
def list_external_player_statistics(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    year: str | None = Query(default=None),
    racer_name: str | None = Query(default=None),
    period_number: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    items, total = repository.list_filtered(
        db,
        offset=(page - 1) * page_size,
        limit=page_size,
        year=year,
        racer_name=racer_name,
        period_number=period_number,
        grade=grade,
    )
    return {
        "items": items,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total),
    }


@router.get(
    "/external-player-statistics/{statistic_id}",
    response_model=ExternalPlayerStatisticRead,
)
def get_external_player_statistic(
    statistic_id: int,
    db: Session = Depends(get_db),
):
    item = repository.get_by_id(db, statistic_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External player statistic not found",
        )
    return item


@router.get(
    "/player-match-candidates",
    response_model=list[PlayerMatchCandidateRead],
)
def list_player_match_candidates(
    year: str | None = Query(default=None),
    racer_name: str | None = Query(default=None),
    period_number: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    match_status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        return PlayerMatchCandidateService().build_report(
            db,
            year=year,
            racer_name=racer_name,
            period_number=period_number,
            grade=grade,
            limit=limit,
            match_status=match_status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
