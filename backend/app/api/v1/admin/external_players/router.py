from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.db.session import get_db
from app.repositories.external_players import ExternalPlayerRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.external_players import ExternalPlayerRead


router = APIRouter(
    prefix="/external-players",
    tags=["admin-external-players"],
    dependencies=[Depends(require_admin)],
)
repository = ExternalPlayerRepository()


@router.get("", response_model=PaginatedResponse[ExternalPlayerRead])
def list_external_players(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source: str | None = Query(default=None),
    name: str | None = Query(default=None),
    period_number: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    items, total = repository.list_filtered(
        db,
        offset=(page - 1) * page_size,
        limit=page_size,
        source=source,
        name=name,
        period_number=period_number,
        grade=grade,
        status=status_filter,
    )
    return {
        "items": items,
        "meta": PaginationMeta(page=page, page_size=page_size, total=total),
    }


@router.get("/{external_player_id}", response_model=ExternalPlayerRead)
def get_external_player(
    external_player_id: int,
    db: Session = Depends(get_db),
):
    item = repository.get_by_id(db, external_player_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External player not found",
        )
    return item
