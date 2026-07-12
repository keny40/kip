from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "auth", "status": "stub", "todo": "Implement JWT login flow later."}
