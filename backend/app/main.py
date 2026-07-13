from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.api.v1.admin.router import router as admin_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.dashboard.router import router as dashboard_router
from app.api.v1.entries.router import router as entries_router
from app.api.v1.players.router import router as players_router
from app.api.v1.predictions.router import router as predictions_router
from app.api.v1.races.router import router as races_router
from app.api.v1.results.router import router as results_router
from app.api.v1.tracks.router import router as tracks_router
from app.api.v1.users.router import router as users_router
from app.core.config import settings

app = FastAPI(
    title="Keirin Intelligence Platform",
    version="0.2.0",
    description="Phase 1 local MVP for keirin data management and analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(races_router, prefix=settings.api_v1_prefix)
app.include_router(players_router, prefix=settings.api_v1_prefix)
app.include_router(entries_router, prefix=settings.api_v1_prefix)
app.include_router(results_router, prefix=settings.api_v1_prefix)
app.include_router(tracks_router, prefix=settings.api_v1_prefix)
app.include_router(predictions_router, prefix=settings.api_v1_prefix)
app.include_router(analytics_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Keirin Intelligence Platform",
        "status": "running",
        "phase": "phase1_local_mvp",
    }
