from fastapi import APIRouter

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "predictions", "status": "stub", "todo": "Implement model orchestration later."}
