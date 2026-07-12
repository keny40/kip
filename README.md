# Keirin Intelligence Platform (KIP)

KIP is a local data analysis MVP demo for keirin racing data.

## Current State

- FastAPI backend
- SQLite demo database
- Alembic head at `0004_admin_auth`
- Flutter Web demo on Chrome
- JWT admin auth for write APIs

## Run Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Create Admin User

After initializing or resetting the demo database, create an admin account before using write APIs:

```bash
python scripts/create_admin.py --email admin@example.com
```

The script prompts for a password twice and stores only a hash in the database.

## Run Flutter Web

```bash
flutter run -d chrome \
  --web-port 5001 \
  --dart-define=KIP_API_BASE_URL=http://127.0.0.1:8000
```

## Environment

- `KIP_API_BASE_URL` controls the Flutter API base URL.
- `CORS_ORIGINS` controls allowed local web origins.
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, and `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` configure backend auth.
- `CSV_IMPORT_MAX_BYTES` limits admin CSV uploads.

## API Access

- Read APIs remain public.
- Create, update, and delete APIs require an admin JWT.
- Admin CSV uploads are available at `/api/v1/admin/imports/{import_type}`.
- In Swagger UI, use `Authorize` with the bearer token returned by `/api/v1/auth/login`.
- Example login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"your-password\"}"
```

## Admin CSV Upload

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/imports/players?dry_run=true" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@samples/players.csv"
```

## Demo DB Reset

```bash
python scripts/reset_demo_db.py
```

This rebuilds the local SQLite demo database and reloads sample data.
Do not use it against a production PostgreSQL database.

## Docker Demo

Run the full local demo with one command:

```bash
docker compose up --build
```

Open:

- http://localhost:5001
- http://localhost:8000
- http://localhost:8000/docs
