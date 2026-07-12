from dataclasses import dataclass
from os import getenv

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5001",
    "http://127.0.0.1:5001",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
)


def parse_cors_origins(value: str | None) -> tuple[str, ...]:
    if value is None:
        return DEFAULT_CORS_ORIGINS

    origins = tuple(origin.strip() for origin in value.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


@dataclass(frozen=True)
class Settings:
    app_name: str = "Keirin Intelligence Platform"
    environment: str = getenv("ENVIRONMENT", "development")
    api_v1_prefix: str = "/api/v1"
    database_url: str = getenv("DATABASE_URL", "sqlite:///./kip.db")
    cors_origins: tuple[str, ...] = parse_cors_origins(getenv("CORS_ORIGINS"))
    redis_url: str = getenv("REDIS_URL", "redis://localhost:6379/0")
    storage_path: str = getenv("STORAGE_PATH", "./storage")
    jwt_secret_key: str = getenv("JWT_SECRET_KEY", "dev-only-local-secret-key-for-kip-demo-2026")
    jwt_algorithm: str = getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    csv_import_max_bytes: int = int(getenv("CSV_IMPORT_MAX_BYTES", "5242880"))


settings = Settings()
