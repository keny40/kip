from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "dashboard", "status": "stub", "todo": "Implement dashboard aggregation later."}
