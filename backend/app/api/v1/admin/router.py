from fastapi import APIRouter

from app.api.v1.admin.external_players.router import router as external_players_router
from app.api.v1.admin.imports.router import router as imports_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(imports_router)
router.include_router(external_players_router)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "admin", "status": "stub", "todo": "Implement admin controls later."}
