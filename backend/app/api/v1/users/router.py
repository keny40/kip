from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"service": "users", "status": "stub", "todo": "Implement user CRUD later."}
