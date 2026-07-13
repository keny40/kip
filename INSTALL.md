# Install

## Backend

1. Install Python 3.12 and activate your virtual environment.
2. Change into `backend/`.
3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Run the API server.

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Apply database migrations.

```bash
alembic upgrade head
```

Current Phase 1 head is `0006_external_player_statistics`.

6. Create an admin account for write access.

```bash
python ../scripts/create_admin.py --email admin@example.com
```

7. Load sample data and reset the local demo database when needed.

```bash
python ../scripts/seed_sample_data.py
python ../scripts/reset_demo_db.py
```

## Frontend

1. Install the Flutter SDK.
2. Change into `frontend/`.
3. Fetch packages.

```bash
flutter pub get
```

4. Run the app in Chrome.

```bash
flutter run -d chrome \
  --web-port 5001 \
  --dart-define=KIP_API_BASE_URL=http://127.0.0.1:8000
```

5. Validate and build the app.

```bash
flutter analyze --no-pub
flutter test --no-pub
flutter build web --no-pub
```

## Environment

- `DATABASE_URL=sqlite:///./kip.db` when commands run from `backend/`
- `DATA_GO_KR_SERVICE_KEY` is required only for data.go collector live calls; never save its value in tracked files or logs.
- `CORS_ORIGINS=http://localhost:5001,http://127.0.0.1:5001,http://localhost:5000,http://127.0.0.1:5000`
- `JWT_SECRET_KEY=dev-only-local-secret-key-for-kip-demo-2026`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `CSV_IMPORT_MAX_BYTES=5242880`

The listed JWT secret is a local development default only. Never use it in an operating environment; inject a strong independent `JWT_SECRET_KEY` through a secret-management mechanism.

## Notes

- The project is currently a local MVP demo.
- The demo database is SQLite-based and rebuilt by `scripts/reset_demo_db.py`.
- Do not use the demo reset flow against a production PostgreSQL database.
- Read APIs are public, but create/update/delete APIs require an admin JWT.
- Admin CSV uploads use `POST /api/v1/admin/imports/{import_type}` with `multipart/form-data`.
- Use `python scripts/create_admin.py --email admin@example.com` after a reset to create the first admin.
- Example login request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"your-password\"}"
```

Admin CSV upload example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/imports/players?dry_run=true" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@samples/players.csv"
```

## Docker Demo

The Compose stack uses PostgreSQL. Copy the example environment file and replace every placeholder secret before running it:

```bash
cp .env.example .env
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
```

This exposes:

- Flutter Web: http://localhost:5001
- FastAPI: http://localhost:8000
- API docs: http://localhost:8000/docs

The default host ports are PostgreSQL `5433`, Backend `8000`, and Flutter Web `5001`. Change `KIP_POSTGRES_PORT`, `KIP_BACKEND_PORT`, or `KIP_FRONTEND_PORT` if they conflict with local services.

The Backend waits for PostgreSQL health, runs `alembic upgrade head`, and optionally runs `scripts/seed_phase2_data.py` when `KIP_SEED_DEMO=1`. The seed requires `KIP_ADMIN_PASSWORD` and never prints it.

Run the destructive PostgreSQL integration test only against the disposable Compose database:

```bash
export POSTGRES_TEST_DATABASE_URL='postgresql+psycopg://kip:URL_ENCODED_PASSWORD@127.0.0.1:5433/kip'
export KIP_ALLOW_POSTGRES_TEST_RESET=1
pytest -m postgres_integration -q
```

Stop containers with `docker compose down`. Use `docker compose down -v` only when the disposable PostgreSQL volume should also be deleted.

This Phase 2 review environment had no Docker CLI, so the Compose build, container health, PostgreSQL migration, and integration test remain unverified here.
