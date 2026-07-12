# Keirin Intelligence Platform (KIP)

KIP is a local data analysis MVP demo for keirin racing data.

## Current State

- FastAPI backend
- SQLite demo database
- Alembic head at `0003_add_tracks`
- Flutter Web demo on Chrome

## Run Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run Flutter Web

```bash
flutter run -d chrome \
  --web-port 5001 \
  --dart-define=KIP_API_BASE_URL=http://127.0.0.1:8000
```

## Environment

- `KIP_API_BASE_URL` controls the Flutter API base URL.
- `CORS_ORIGINS` controls allowed local web origins.

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
