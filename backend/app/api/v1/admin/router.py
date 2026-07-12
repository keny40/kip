from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "admin", "status": "stub", "todo": "Implement admin controls later."}
